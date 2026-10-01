"""The decision engine.

A pure function of inputs, configuration and the previous state. It never
touches Home Assistant and it never writes anything: it returns a
:class:`SystemDecision` describing what should happen and why. The caller is
responsible for turning that into register writes.

Two conventions run through all of it. A value of ``None`` for a register means
"do not write this", which is not the same as writing zero or false, and is how
the compressor lockout expresses itself. And no rule branches on the mode name:
each one reads the gate it cares about, so that deriving the mode automatically
later changes where it comes from and not what anything does with it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any

from .const import (
    CO2_DWELL,
    CONF_AUX_HEAT_BELOW,
    CONF_AUX_HEAT_OFF_AT_NIGHT,
    CONF_CO2_HIGH,
    CONF_COOL_RELEASE_ABOVE,
    CONF_FAN_AIR_QUALITY,
    CONF_FAN_BOOST,
    CONF_FAN_HOLIDAY,
    CONF_FAN_NIGHT,
    CONF_FAN_NIGHT_COOLING,
    CONF_FAN_NORMAL,
    CONF_FAN_QUIET_MAX,
    CONF_FORECAST_BLOCKS_ABOVE,
    CONF_FROST_PROTECTION_BELOW,
    CONF_HEAT_RELEASE_BELOW,
    CONF_HUMIDITY_HIGH,
    CONF_NIGHT_END,
    CONF_NIGHT_START,
    CONF_PV_SURPLUS_ABOVE,
    CONF_PV_TARGET_BOOST,
    CONF_RELEASE_HYSTERESIS,
    CONF_TARGET_COOL,
    CONF_TARGET_COOL_HOLIDAY,
    CONF_TARGET_COOL_WINDOW_OPEN,
    CONF_TARGET_HOLIDAY,
    CONF_TARGET_NIGHT,
    CONF_TARGET_NORMAL,
    CONF_TARGET_WINDOW_OPEN,
    CONTACT_DWELL,
    FAN_MAX,
    FAN_MIN,
    OUTDOOR_MAX_AGE,
    PV_SURPLUS_DWELL,
    RELEASE_LOCKOUT,
    TARGET_MAX,
    TARGET_MIN,
    TARGET_RESOLUTION,
    ActuatorKind,
    FanMode,
    FanReason,
    HeatingCoolingFunction,
    Intent,
    Mode,
    Reason,
    RoomIntent,
    RoomReason,
)
from .models import EffectiveConfig, Gate, Reading, RoomDecision, SystemDecision


@dataclass(frozen=True, slots=True)
class RoomInputs:
    """Everything the engine is allowed to know about one room.

    ``None`` for an optional reading means the sensor was never configured,
    which is not a failure. A configured sensor that cannot be read arrives as a
    :class:`Reading` with no value, and that is a failure the record names.
    """

    room_id: str
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    temperature: Reading = Reading()
    contacts: tuple[Reading, ...] = ()
    humidity: Reading | None = None
    co2: Reading | None = None
    #: What heats the room, which decides what its hvac mode means.
    actuator: ActuatorKind = ActuatorKind.WGT_ROOM


@dataclass(frozen=True, slots=True)
class Inputs:
    """Everything the engine is allowed to look at."""

    now: datetime
    outdoor: Reading = Reading()
    forecast_max: Reading | None = None
    pv_power: Reading | None = None
    #: The releases as the device reports them, with how long they have held.
    heat_release: Reading = Reading()
    cool_release: Reading = Reading()
    #: While the compressor stands still a release may change freely, which is
    #: the other half of the lockout.
    compressor_running: Reading = Reading()
    rooms: tuple[RoomInputs, ...] = ()


@dataclass(frozen=True, slots=True)
class EngineState:
    """Runtime state carried between evaluations.

    Only what cannot be read back from an entity belongs here. Both of these
    are "since when has this held", which no sensor reports.
    """

    co2_high_since: Mapping[str, datetime] = field(default_factory=dict)
    pv_surplus_since: datetime | None = None


def _parse_time(value: str) -> time:
    hour, _, minute = str(value).partition(":")
    return time(int(hour), int(minute or 0))


def _is_night(config: EffectiveConfig, now: datetime) -> bool:
    """Whether now falls in the configured night window.

    The window normally wraps midnight, which is why this is not a plain
    comparison.
    """
    start = _parse_time(config.get(CONF_NIGHT_START))
    end = _parse_time(config.get(CONF_NIGHT_END))
    current = now.time()
    if start > end:
        return current >= start or current < end
    return start <= current < end


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _quantize(value: float) -> float:
    """Round a setpoint to the resolution the device stores it at.

    What the device reports is always an exact tenth, because it is a register
    divided by ten. A sum computed here is not: adding a boost to a configured
    setpoint lands on an inexact tenth for about one in five combinations across
    the configurable range, 10.1 plus 0.2 giving 10.299999999999999 among them.
    A writer that compares the two and writes when they differ would write that
    register on every evaluation for as long as the condition held.

    None of the pairs a heating setpoint and a plausible boost produce actually
    hit it today. This is here so that holds for every input rather than for the
    ones that happen to be exact.
    """
    return round(value / TARGET_RESOLUTION) * TARGET_RESOLUTION


def _window_open(contacts: tuple[Reading, ...]) -> tuple[bool, list[str]]:
    """Whether any contact reports open, and which ones could not be read.

    A contact that cannot be read counts as open. Heating against an open
    window is the more expensive mistake, and a dead reed switch is exactly the
    failure that hid in v1.
    """
    failed: list[str] = []
    is_open = False
    for index, contact in enumerate(contacts):
        if contact.missing:
            failed.append(f"contact[{index}]")
            is_open = True
            continue
        if not contact.value:
            continue
        # A contact that has only just opened is still a hand on a handle.
        if contact.stable_for is None or contact.stable_for >= CONTACT_DWELL:
            is_open = True
    return is_open, failed


def _track_co2(
    inputs: Inputs, hub: dict[str, Any], state: EngineState
) -> dict[str, datetime]:
    """Carry forward, per room, since when CO₂ has been above the threshold.

    Tracked before any early return, so that a controller switched off for ten
    minutes does not hand the fan a fresh dwell timer when it comes back.
    """
    tracked: dict[str, datetime] = {}
    for room in inputs.rooms:
        if room.co2 is None:
            continue
        reading = room.co2.as_number()
        if reading is None:
            continue
        threshold = EffectiveConfig(hub, room.config).number(CONF_CO2_HIGH)
        if reading <= threshold:
            continue
        tracked[room.room_id] = state.co2_high_since.get(room.room_id, inputs.now)
    return tracked


def _track_pv(inputs: Inputs, hub: dict[str, Any], state: EngineState) -> datetime | None:
    """Carry forward since when PV surplus has held."""
    if inputs.pv_power is None:
        return None
    power = inputs.pv_power.as_number()
    if power is None:
        return state.pv_surplus_since
    if power < EffectiveConfig(hub).number(CONF_PV_SURPLUS_ABOVE):
        return None
    return state.pv_surplus_since or inputs.now


def _frost_rooms(inputs: Inputs, hub: dict[str, Any]) -> tuple[str, ...]:
    """Rooms that have fallen below their frost limit, named for the record.

    A room with an open window is not one of them. It is cold on purpose, and
    letting it force the heating mode would have the coldest room in the house
    release the heat pump for every other room, all winter, because somebody
    sleeps with the window open. Heating against an open window is not frost
    protection wherever it is decided.
    """
    cold: list[str] = []
    for room in inputs.rooms:
        value = room.temperature.as_number()
        if value is None:
            continue
        if _window_open(room.contacts)[0]:
            continue
        limit = EffectiveConfig(hub, room.config).number(CONF_FROST_PROTECTION_BELOW)
        if value < limit:
            cold.append(f"{room.name} at {value} °C below {limit} °C")
    return tuple(cold)


def _resolve_mode(
    requested: Mode, inputs: Inputs, frost: tuple[str, ...]
) -> tuple[Mode, Gate, list[str]]:
    """The mode that can actually be acted on.

    Heating and cooling both need a current outdoor reading: one to decide the
    release, the other to know whether outside air is worth having. Without one,
    ventilation is the honest answer, and it is the one state that cannot be
    wrong for lack of data.

    Frost protection comes before both. It is the one thing that overrides what
    was asked for, including the fallback, because a missing outdoor reading is
    exactly the situation in which a freezing house most needs heat.
    """
    degraded: list[str] = []
    usable = not inputs.outdoor.stale(OUTDOOR_MAX_AGE)
    if usable:
        outdoor_gate = Gate("outdoor_usable", True, "")
    else:
        degraded.append("outdoor")
        age = inputs.outdoor.updated_ago
        outdoor_gate = Gate(
            "outdoor_usable",
            False,
            "never reported"
            if age is None
            else f"last reported {age.total_seconds() / 60:.0f} min ago",
        )

    if frost:
        return Mode.HEATING, outdoor_gate, degraded
    if not usable and requested is not Mode.VENTILATION:
        return Mode.VENTILATION, outdoor_gate, degraded
    return requested, outdoor_gate, degraded


def _release(
    *,
    wanted: bool,
    current: Reading,
    compressor: Reading,
) -> tuple[bool | None, Gate]:
    """Apply the compressor lockout to a release the rules want changed.

    The release is only moved when it has been stable long enough, or when the
    compressor is not running anyway. Returning ``None`` writes nothing, which
    leaves the device where it is and says so in the record.
    """
    if current.missing or bool(current.value) == wanted:
        # Nothing to change. Writing the value it already has is what the diff
        # in the coordinator drops, so there is no lockout to apply.
        return wanted, Gate("release_lockout", True, "unchanged")

    running = bool(compressor.value) if not compressor.missing else True
    held = current.stable_for
    stable_enough = held is not None and held >= RELEASE_LOCKOUT
    if stable_enough or not running:
        detail = "compressor idle" if not running else "stable long enough"
        return wanted, Gate("release_lockout", True, detail)

    minutes = 0.0 if held is None else held.total_seconds() / 60
    return None, Gate(
        "release_lockout",
        False,
        f"changed {minutes:.0f} min ago and the compressor is running",
    )


def _heat_wanted(
    config: EffectiveConfig, inputs: Inputs, *, frost: bool
) -> tuple[bool, Reason, list[Gate]]:
    """Whether the heat pump should be released, and why."""
    if frost:
        # Neither the threshold nor the forecast gets a say here. The house is
        # already too cold, which is the one case that needs no further test.
        return True, Reason.FROST_PROTECTION, [
            Gate("frost_protection", False, "a room is below its frost limit")
        ]

    outdoor = inputs.outdoor.as_number()
    threshold = config.number(CONF_HEAT_RELEASE_BELOW)
    hysteresis = config.number(CONF_RELEASE_HYSTERESIS)
    released = not inputs.heat_release.missing and bool(inputs.heat_release.value)

    # The hysteresis sits on the releasing side only: once it is on, it takes a
    # whole band of warming to turn it off again.
    limit = threshold + hysteresis if released else threshold
    wanted = outdoor is not None and outdoor < limit
    gates = [
        Gate(
            "outdoor_cold",
            wanted,
            f"{outdoor} < {limit}" if outdoor is not None else "no reading",
        )
    ]

    forecast = None if inputs.forecast_max is None else inputs.forecast_max.as_number()
    if wanted and forecast is not None and outdoor is not None:
        # A cold morning under a warm forecast does not need the compressor, but
        # a genuinely cold day does, so the forecast only gets a say once it is
        # not actually cold out.
        floor = config.number(CONF_FORECAST_BLOCKS_ABOVE)
        if outdoor >= floor and forecast >= threshold:
            gates.append(
                Gate("forecast_cold", False, f"forecast high {forecast} >= {threshold}")
            )
            return False, Reason.FORECAST_WARM, gates
        gates.append(Gate("forecast_cold", True, f"forecast high {forecast}"))

    return (
        wanted,
        Reason.HEAT_RELEASED if wanted else Reason.HEAT_TOO_WARM,
        gates,
    )


def _warmest_room(inputs: Inputs) -> tuple[float | None, str | None]:
    """The highest room temperature that could be read, and whose it is."""
    warmest: float | None = None
    whose: str | None = None
    for room in inputs.rooms:
        value = room.temperature.as_number()
        if value is None:
            continue
        if warmest is None or value > warmest:
            warmest, whose = value, room.name
    return warmest, whose


def _cool_wanted(
    config: EffectiveConfig, inputs: Inputs
) -> tuple[bool, Reason, list[Gate], str | None]:
    """Whether the heat pump should be released for cooling, and why."""
    warmest, whose = _warmest_room(inputs)
    threshold = config.number(CONF_COOL_RELEASE_ABOVE)
    hysteresis = config.number(CONF_RELEASE_HYSTERESIS)
    released = not inputs.cool_release.missing and bool(inputs.cool_release.value)

    limit = threshold - hysteresis if released else threshold
    wanted = warmest is not None and warmest > limit
    gate = Gate(
        "room_too_warm",
        wanted,
        f"{whose} at {warmest} > {limit}" if warmest is not None else "no reading",
    )
    return (
        wanted,
        Reason.COOL_RELEASED if wanted else Reason.COOL_NOT_NEEDED,
        [gate],
        whose if wanted else None,
    )


#: Settings that belong to the unit rather than to a room, recorded with the
#: system decision so the numbers behind a release are in the record too.
SYSTEM_SETTINGS: tuple[str, ...] = (
    CONF_HEAT_RELEASE_BELOW,
    CONF_RELEASE_HYSTERESIS,
    CONF_FORECAST_BLOCKS_ABOVE,
    CONF_COOL_RELEASE_ABOVE,
    CONF_FAN_NORMAL,
    CONF_FAN_NIGHT,
    CONF_FAN_HOLIDAY,
    CONF_FAN_QUIET_MAX,
    CONF_FAN_BOOST,
    CONF_FAN_AIR_QUALITY,
    CONF_FAN_NIGHT_COOLING,
    CONF_PV_SURPLUS_ABOVE,
    CONF_PV_TARGET_BOOST,
    CONF_NIGHT_START,
    CONF_NIGHT_END,
)


def _room_decision(
    room: RoomInputs,
    hub: dict[str, Any],
    *,
    now: datetime,
    enabled: bool,
    mode: Mode,
    holiday: bool,
    heating_active: bool,
    outdoor: float | None,
    pv_surplus: bool,
) -> RoomDecision:
    """Decide one room's setpoint and whether its auxiliary heater may run."""
    config = EffectiveConfig(hub, room.config)
    settings = config.snapshot()
    raw = {
        "temperature": room.temperature.as_dict(),
        "contacts": [contact.as_dict() for contact in room.contacts],
        "humidity": None if room.humidity is None else room.humidity.as_dict(),
        "co2": None if room.co2 is None else room.co2.as_dict(),
    }

    if not enabled:
        return RoomDecision(
            room_id=room.room_id,
            name=room.name,
            intent=RoomIntent.DISABLED,
            reason=RoomReason.CONTROLLER_DISABLED,
            message="Controller is off, nothing is written",
            inputs=raw,
            settings=settings,
        )

    window_open, failed_contacts = _window_open(room.contacts)
    night = _is_night(config, now)
    degraded = [f"{room.room_id}.{name}" for name in failed_contacts]

    temperature = room.temperature.as_number()
    if temperature is None:
        degraded.append(f"{room.room_id}.temperature")
    for name, reading in (("humidity", room.humidity), ("co2", room.co2)):
        if reading is not None and reading.missing:
            degraded.append(f"{room.room_id}.{name}")

    gates = [
        Gate(
            "window_closed",
            not window_open,
            "contact unreadable" if failed_contacts else ("open" if window_open else "closed"),
        ),
        Gate("night", night, f"{config.get(CONF_NIGHT_START)} to {config.get(CONF_NIGHT_END)}"),
    ]

    if mode is Mode.COOLING:
        if window_open:
            target = config.number(CONF_TARGET_COOL_WINDOW_OPEN)
            intent, reason = RoomIntent.WINDOW_OPEN, RoomReason.WINDOW_OPEN
        elif holiday:
            target = config.number(CONF_TARGET_COOL_HOLIDAY)
            intent, reason = RoomIntent.COOLING, RoomReason.HOLIDAY
        else:
            target = config.number(CONF_TARGET_COOL)
            intent, reason = RoomIntent.COOLING, RoomReason.COOLING
    else:
        if window_open:
            target = config.number(CONF_TARGET_WINDOW_OPEN)
            intent, reason = RoomIntent.WINDOW_OPEN, RoomReason.WINDOW_OPEN
        elif holiday:
            target = config.number(CONF_TARGET_HOLIDAY)
            intent, reason = RoomIntent.HOLIDAY, RoomReason.HOLIDAY
        elif night:
            target = config.number(CONF_TARGET_NIGHT)
            intent, reason = RoomIntent.NIGHT, RoomReason.NIGHT_SETBACK
        else:
            target = config.number(CONF_TARGET_NORMAL)
            intent, reason = RoomIntent.NORMAL, RoomReason.NORMAL

        # Surplus is only worth storing in a house that is occupied and shut.
        # Dumping it into an empty room or one with the window open is paying
        # attention to the inverter instead of to the house.
        if mode is Mode.HEATING and pv_surplus and not window_open and not holiday:
            target += config.number(CONF_PV_TARGET_BOOST)
            reason = RoomReason.PV_SURPLUS

        if mode is Mode.VENTILATION:
            # The setpoint is still written, so the device shows a sensible
            # number and means it again the moment heating is allowed.
            intent = RoomIntent.IDLE

    # Rounded to what the device can store, so that the value the engine means
    # and the value it will read back are the same number.
    target = _quantize(_clamp(target, TARGET_MIN, TARGET_MAX))

    auxiliary: bool | None = None
    heating_enabled: bool | None = None
    if room.actuator is ActuatorKind.WGT_ROOM:
        aux_below = config.number(CONF_AUX_HEAT_BELOW)
        off_at_night = bool(config.get(CONF_AUX_HEAT_OFF_AT_NIGHT))
        cold_enough = outdoor is not None and outdoor < aux_below
        auxiliary = (
            mode is Mode.HEATING
            and heating_active
            and cold_enough
            and not window_open
            and not (night and off_at_night)
            # Without a room temperature there is no way to tell whether the
            # second stage is needed, and the expensive one stays off.
            and temperature is not None
        )
        gates.append(
            Gate(
                "aux_outdoor_cold",
                cold_enough,
                f"{outdoor} < {aux_below}" if outdoor is not None else "no reading",
            )
        )
        if off_at_night:
            gates.append(Gate("aux_allowed_now", not night, "off at night in this room"))
    else:
        # A heater of its own regulates its room; all this decides is whether it
        # may run. The setpoint already carries holiday and the night setback.
        heating_enabled = mode is Mode.HEATING and not window_open
        gates.append(Gate("heating_allowed", heating_enabled, f"mode is {mode}"))

    message = _room_message(
        reason=reason,
        intent=intent,
        target=target,
        auxiliary=auxiliary,
        heating_enabled=heating_enabled,
        config=config,
        temperature=temperature,
        outdoor=outdoor,
    )

    return RoomDecision(
        room_id=room.room_id,
        name=room.name,
        intent=intent,
        reason=reason,
        message=message,
        target_temperature=target,
        auxiliary_heat=auxiliary,
        heating_enabled=heating_enabled,
        window_open=window_open,
        gates=tuple(gates),
        inputs=raw,
        settings=settings,
        degraded=tuple(degraded),
    )


def _room_message(
    *,
    reason: RoomReason,
    intent: RoomIntent,
    target: float,
    auxiliary: bool | None,
    heating_enabled: bool | None,
    config: EffectiveConfig,
    temperature: float | None,
    outdoor: float | None,
) -> str:
    """One sentence saying what this room is doing and why."""
    if reason is RoomReason.WINDOW_OPEN:
        head = f"Window open, target {target} °C"
    elif reason is RoomReason.HOLIDAY:
        head = f"Holiday, target {target} °C"
    elif reason is RoomReason.NIGHT_SETBACK:
        head = f"Night setback, target {target} °C"
    elif reason is RoomReason.COOLING:
        head = f"Cooling to {target} °C"
    elif reason is RoomReason.PV_SURPLUS:
        boost = config.number(CONF_PV_TARGET_BOOST)
        head = f"PV surplus, target raised by {boost} K to {target} °C"
    else:
        head = f"Target {target} °C"

    if temperature is not None:
        head += f" (now {temperature} °C)"
    if intent is RoomIntent.IDLE:
        head += ", nothing heating or cooling"
    if auxiliary:
        head += f", auxiliary heater on because outdoor {outdoor} °C"
    if heating_enabled is False:
        head += ", heater off"
    return head


def _fan_level(
    rooms: tuple[RoomDecision, ...],
    inputs: Inputs,
    hub: dict[str, Any],
    *,
    mode: Mode,
    fan_request: FanMode | int,
    holiday: bool,
    is_night: bool,
    co2_high_since: Mapping[str, datetime],
) -> tuple[int, FanReason, str | None, int | None]:
    """Decide the one fan level the whole unit runs at.

    Humidity and CO₂ are measured per room but there is a single fan, so the
    rooms compete and the decision names the one that won.
    """
    config = EffectiveConfig(hub)

    if not isinstance(fan_request, FanMode):
        # An explicit stage is the hammer, including stage 0 even though that
        # closes the bypass. Asking for it is answer enough.
        return int(_clamp(int(fan_request), FAN_MIN, FAN_MAX)), FanReason.FIXED_STAGE, None, None

    by_id = {room.room_id: room for room in rooms}
    air_quality = int(config.number(CONF_FAN_AIR_QUALITY))

    # A room with the window open is measuring outdoors, so it asks for nothing.
    def open_window(room_id: str) -> bool:
        room = by_id.get(room_id)
        return room is not None and room.window_open

    level: int
    reason: FanReason
    requested_by: str | None = None

    co2_room = next(
        (
            room
            for room in inputs.rooms
            if room.room_id in co2_high_since
            and not open_window(room.room_id)
            and inputs.now - co2_high_since[room.room_id] >= CO2_DWELL
        ),
        None,
    )
    humid_room = next(
        (
            room
            for room in inputs.rooms
            if room.humidity is not None
            and not open_window(room.room_id)
            and (value := room.humidity.as_number()) is not None
            and value > EffectiveConfig(hub, room.config).number(CONF_HUMIDITY_HIGH)
        ),
        None,
    )
    warmest, _ = _warmest_room(inputs)
    outdoor = inputs.outdoor.as_number()
    night_cooling = (
        mode is Mode.COOLING
        and is_night
        and outdoor is not None
        and warmest is not None
        and outdoor < warmest
    )

    if co2_room is not None:
        level, reason, requested_by = air_quality, FanReason.CO2_HIGH, co2_room.name
    elif humid_room is not None:
        level, reason, requested_by = air_quality, FanReason.HUMIDITY_HIGH, humid_room.name
    elif night_cooling:
        level, reason = int(config.number(CONF_FAN_NIGHT_COOLING)), FanReason.NIGHT_COOLING
    elif holiday:
        level, reason = int(config.number(CONF_FAN_HOLIDAY)), FanReason.HOLIDAY
    elif is_night:
        level, reason = int(config.number(CONF_FAN_NIGHT)), FanReason.NIGHT
    else:
        level, reason = int(config.number(CONF_FAN_NORMAL)), FanReason.NORMAL

    capped_from: int | None = None
    if fan_request is FanMode.BOOST:
        boost = int(config.number(CONF_FAN_BOOST))
        if boost > level:
            level, reason, requested_by = boost, FanReason.BOOST, None
    elif fan_request is FanMode.QUIET:
        ceiling = int(config.number(CONF_FAN_QUIET_MAX))
        if level > ceiling:
            capped_from, level = level, ceiling

    if mode is Mode.COOLING and level < 1:
        # Stage 0 shuts the bypass damper, so asking for it while cooling is
        # asking for the opposite of what the mode is for.
        if capped_from is None:
            capped_from = level
        level = 1

    return int(_clamp(level, FAN_MIN, FAN_MAX)), reason, requested_by, capped_from


def evaluate(
    inputs: Inputs,
    hub: dict[str, Any],
    state: EngineState,
    *,
    enabled: bool,
    mode: Mode,
    fan_request: FanMode | int,
    holiday: bool,
) -> tuple[SystemDecision, EngineState]:
    """Evaluate the unit and every room, and return the decision plus state."""
    # The dwell timers are carried forward before anything can return early, so
    # that a controller switched off for ten minutes does not come back with a
    # fresh timer and a fan that has forgotten the bathroom.
    new_state = EngineState(
        co2_high_since=_track_co2(inputs, hub, state),
        pv_surplus_since=_track_pv(inputs, hub, state),
    )
    config = EffectiveConfig(hub)
    raw = {
        "outdoor": inputs.outdoor.as_dict(),
        "forecast_max": None if inputs.forecast_max is None else inputs.forecast_max.as_dict(),
        "pv_power": None if inputs.pv_power is None else inputs.pv_power.as_dict(),
        "heat_release": inputs.heat_release.as_dict(),
        "cool_release": inputs.cool_release.as_dict(),
        "compressor_running": inputs.compressor_running.as_dict(),
    }
    settings = config.snapshot(SYSTEM_SETTINGS)

    if not enabled:
        rooms = tuple(
            _room_decision(
                room,
                hub,
                now=inputs.now,
                enabled=False,
                mode=mode,
                holiday=holiday,
                heating_active=False,
                outdoor=None,
                pv_surplus=False,
            )
            for room in inputs.rooms
        )
        return (
            SystemDecision(
                timestamp=inputs.now,
                intent=Intent.DISABLED,
                reason=Reason.CONTROLLER_DISABLED,
                message="Controller is off, no register is written",
                mode=mode,
                requested_mode=mode,
                holiday=holiday,
                rooms=rooms,
                inputs=raw,
                settings=settings,
            ),
            new_state,
        )

    frost = _frost_rooms(inputs, hub)
    effective_mode, outdoor_gate, degraded = _resolve_mode(mode, inputs, frost)
    gates = [outdoor_gate, Gate("frost_protection", not frost, "; ".join(frost))]
    outdoor = inputs.outdoor.as_number()

    heat_release: bool | None = None
    cool_release: bool | None = None
    reason: Reason
    fan_requested_by: str | None

    if effective_mode is Mode.HEATING:
        wanted, reason, heat_gates = _heat_wanted(config, inputs, frost=bool(frost))
        gates.extend(heat_gates)
        heat_release, lockout = _release(
            wanted=wanted,
            current=inputs.heat_release,
            compressor=inputs.compressor_running,
        )
        gates.append(lockout)
        cool_release = False
        function = HeatingCoolingFunction.HEATING
        intent = Intent.HEATING
        if heat_release is None:
            reason = Reason.RELEASE_LOCKED
    elif effective_mode is Mode.COOLING:
        wanted, reason, cool_gates, _ = _cool_wanted(config, inputs)
        gates.extend(cool_gates)
        cool_release, lockout = _release(
            wanted=wanted,
            current=inputs.cool_release,
            compressor=inputs.compressor_running,
        )
        gates.append(lockout)
        heat_release = False
        # The damper only opens while this reads cooling, so the mode owns it.
        function = HeatingCoolingFunction.COOLING
        intent = Intent.COOLING
        if cool_release is None:
            reason = Reason.RELEASE_LOCKED
    else:
        heat_release = False
        cool_release = False
        function = HeatingCoolingFunction.OFF
        intent = Intent.VENTILATION
        reason = (
            Reason.OUTDOOR_UNAVAILABLE
            if effective_mode is not mode
            else Reason.VENTILATION_ONLY
        )

    heating_active = (
        heat_release
        if heat_release is not None
        else (not inputs.heat_release.missing and bool(inputs.heat_release.value))
    )
    pv_surplus = (
        new_state.pv_surplus_since is not None
        and inputs.now - new_state.pv_surplus_since >= PV_SURPLUS_DWELL
    )
    is_night = _is_night(config, inputs.now)

    rooms = tuple(
        _room_decision(
            room,
            hub,
            now=inputs.now,
            enabled=True,
            mode=effective_mode,
            holiday=holiday,
            heating_active=bool(heating_active),
            outdoor=outdoor,
            pv_surplus=pv_surplus,
        )
        for room in inputs.rooms
    )
    for room in rooms:
        degraded.extend(room.degraded)

    fan_level, fan_reason, fan_requested_by, fan_capped_from = _fan_level(
        rooms,
        inputs,
        hub,
        mode=effective_mode,
        fan_request=fan_request,
        holiday=holiday,
        is_night=is_night,
        co2_high_since=new_state.co2_high_since,
    )

    decision = SystemDecision(
        timestamp=inputs.now,
        intent=intent,
        reason=reason,
        message=_system_message(
            reason=reason,
            mode=effective_mode,
            requested=mode,
            frost=frost,
            outdoor=outdoor,
            config=config,
            fan_level=fan_level,
            fan_reason=fan_reason,
            fan_requested_by=fan_requested_by,
            fan_capped_from=fan_capped_from,
        ),
        mode=effective_mode,
        requested_mode=mode,
        holiday=holiday,
        heat_release=heat_release,
        cool_release=cool_release,
        heating_cooling_function=function,
        fan_level=fan_level,
        fan_reason=fan_reason,
        fan_requested_by=fan_requested_by,
        fan_capped_from=fan_capped_from,
        is_night=is_night,
        rooms=rooms,
        gates=tuple(gates),
        inputs=raw,
        settings=settings,
        degraded=tuple(dict.fromkeys(degraded)),
    )
    return decision, new_state


def _system_message(
    *,
    reason: Reason,
    mode: Mode,
    requested: Mode,
    frost: tuple[str, ...],
    outdoor: float | None,
    config: EffectiveConfig,
    fan_level: int,
    fan_reason: FanReason,
    fan_requested_by: str | None,
    fan_capped_from: int | None,
) -> str:
    """One sentence for the system decision."""
    threshold = config.number(CONF_HEAT_RELEASE_BELOW)
    if reason is Reason.FROST_PROTECTION:
        head = f"Frost protection, {'; '.join(frost)}"
    elif reason is Reason.HEAT_RELEASED:
        head = f"Heating released, outdoor {outdoor} °C below {threshold} °C"
    elif reason is Reason.HEAT_TOO_WARM:
        head = f"Heating blocked, outdoor {outdoor} °C at or above {threshold} °C"
    elif reason is Reason.FORECAST_WARM:
        head = f"Heating blocked, the day is forecast to reach {threshold} °C"
    elif reason is Reason.COOL_RELEASED:
        head = f"Cooling released, a room is above {config.number(CONF_COOL_RELEASE_ABOVE)} °C"
    elif reason is Reason.COOL_NOT_NEEDED:
        head = "Cooling allowed but no room is warm enough to need it"
    elif reason is Reason.RELEASE_LOCKED:
        head = "Release left alone, it changed less than 30 min ago and the compressor is running"
    elif reason is Reason.OUTDOOR_UNAVAILABLE:
        head = f"{requested} asked for, ventilation only because the outdoor reading is unusable"
    else:
        head = "Ventilation only, neither heating nor cooling allowed"

    fan = f"fan {fan_level}"
    if fan_requested_by is not None:
        fan += f" for {fan_requested_by}"
    fan += f" ({fan_reason})"
    if fan_capped_from is not None:
        fan += f", capped from {fan_capped_from}"
    return f"{head}. Mode {mode}, {fan}"
