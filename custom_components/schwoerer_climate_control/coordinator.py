"""Scheduling, reading, diffing and writing.

This is the only place that writes, and it writes as little as it can. Three
rules carry that, and all three exist because v1 broke the device by ignoring
them:

Only what differs is written. In a steady state that is nothing at all.

What it differs from is the value the device reports, never a memory of what was
sent. A write that did not arrive is therefore attempted again by itself, and one
that never arrives is counted and reported.

A value the device is not currently reporting is not a difference. After a
restart or a failed poll the current value is unknown, and writing then would
mean rewriting every register every time Home Assistant starts.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import (
    device_registry as dr,
)
from homeassistant.helpers import (
    entity_registry as er,
)
from homeassistant.helpers import (
    issue_registry as ir,
)
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .adapters import Write, generic, schwoerer
from .const import (
    CONF_ACTUATOR,
    CONF_CLIMATE_ENTITY,
    CONF_CO2_SENSOR,
    CONF_COMPRESSOR_SENSOR,
    CONF_CONTACTS,
    CONF_COOL_RELEASE_SWITCH,
    CONF_DRY_RUN,
    CONF_FORECAST_ENTITY,
    CONF_HEAT_RELEASE_SWITCH,
    CONF_HUMIDITY_SENSOR,
    CONF_NAME,
    CONF_NOTIFY_SERVICE,
    CONF_OPERATION_MODE_SELECT,
    CONF_OUTDOOR_SENSOR,
    CONF_PV_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    DECISION_HISTORY,
    DEGRADED_GRACE,
    DOMAIN,
    EVALUATION_DEBOUNCE,
    EVENT_DECISION,
    ISSUE_INPUT_UNAVAILABLE,
    ISSUE_OPERATION_MODE,
    ISSUE_STUCK_WRITE,
    MIN_WRITE_INTERVAL,
    NOTIFY_WINDOW,
    STUCK_AFTER,
    SUBENTRY_TYPE_ROOM,
    TICK_INTERVAL,
    WRITE_SPACING,
    ActuatorKind,
    FanMode,
    Mode,
    Reason,
)
from .engine import EngineState, Inputs, RoomInputs, evaluate
from .models import Reading, SystemDecision

_LOGGER = logging.getLogger(__name__)

type ClimateControlConfigEntry = ConfigEntry[ClimateControlCoordinator]

#: What the unit's operating mode has to read for the decisions to hold. Written
#: by nobody here; a repair says so when it reads something else.
REQUIRED_OPERATION_MODE = "manual"


@dataclass(slots=True)
class RoomRuntime:
    """One configured room, as the coordinator holds it."""

    subentry_id: str
    title: str
    config: dict[str, Any]

    @property
    def room_id(self) -> str:
        """A short name for logs, write labels and the degraded list."""
        return slugify(self.title)

    @property
    def actuator(self) -> ActuatorKind:
        return ActuatorKind(self.config.get(CONF_ACTUATOR, ActuatorKind.WGT_ROOM))

    @property
    def climate_entity(self) -> str | None:
        return self.config.get(CONF_CLIMATE_ENTITY)


class ClimateControlCoordinator(DataUpdateCoordinator[SystemDecision]):
    """Evaluates the engine on a schedule and carries out what it decides."""

    def __init__(self, hass: HomeAssistant, entry: ClimateControlConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=TICK_INTERVAL,
            # Deliberately not immediate: a contact that chatters, or six rooms
            # reporting within a second of each other, is one evaluation.
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=EVALUATION_DEBOUNCE.total_seconds(),
                immediate=False,
            ),
        )
        self.entry = entry
        self.hub_device_id: str | None = None
        self.rooms: dict[str, RoomRuntime] = {}

        # Controls. Each one is restored by its own entity on startup.
        self.enabled = True
        # Ventilation on a fresh install, because it writes nothing that heats
        # or cools, and frost protection still covers the floor.
        self.mode = Mode.VENTILATION
        self.holiday = False
        self.fan_request: FanMode | int = FanMode.AUTOMATIC
        # Starts from the configuration and is then held here, so the switch can
        # turn it off without a reload. On for a fresh install.
        self.dry_run = bool({**entry.data, **entry.options}.get(CONF_DRY_RUN, True))

        self.engine_state = EngineState()
        self._unsubscribe: list[Any] = []
        self._last_write: datetime | None = None
        self._attempted: set[str] = set()
        self._stuck: dict[str, int] = {}
        self._rate_limited = False
        self._evaluated = False

        self.history: deque[SystemDecision] = deque(maxlen=DECISION_HISTORY)
        self._signatures: dict[str, tuple] = {}
        self._degraded_since: datetime | None = None
        self._pending: list[str] = []
        self._notify_scheduled = False

    ############################################################################
    # Configuration

    @property
    def hub_config(self) -> dict[str, Any]:
        """The hub's settings, options layered over the initial data."""
        return {**self.entry.data, **self.entry.options}

    def load_rooms(self) -> None:
        """Rebuild the room runtimes from the entry's subentries."""
        self.rooms = {
            subentry_id: RoomRuntime(
                subentry_id=subentry_id,
                title=_subentry_title(subentry),
                config=dict(subentry.data),
            )
            for subentry_id, subentry in self.entry.subentries.items()
            if subentry.subentry_type == SUBENTRY_TYPE_ROOM
        }

    def register_hub_device(self) -> str:
        """Register the central device and remember its id for the rooms."""
        entry = dr.async_get(self.hass).async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.entry.title,
            manufacturer="Schwörer Climate Control",
            model="Controller",
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        self.hub_device_id = entry.id
        return entry.id

    ############################################################################
    # Controls

    async def async_set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        await self.async_request_refresh()

    async def async_set_mode(self, mode: Mode) -> None:
        self.mode = mode
        await self.async_request_refresh()

    async def async_set_holiday(self, holiday: bool) -> None:
        self.holiday = holiday
        await self.async_request_refresh()

    async def async_set_fan_request(self, request: FanMode | int) -> None:
        self.fan_request = request
        await self.async_request_refresh()

    async def async_set_dry_run(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        await self.async_request_refresh()

    ############################################################################
    # Reading

    def _state_reading(self, entity_id: str | None) -> Reading | None:
        """A reading for one entity, or None when none is configured.

        None and an empty Reading are different answers: nothing was asked for,
        against something was asked for and could not be read.
        """
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return Reading()
        now = dt_util.utcnow()
        return Reading(
            value=state.state,
            updated_ago=now - state.last_updated,
            stable_for=now - state.last_changed,
        )

    def _number(self, entity_id: str | None) -> Reading | None:
        """A numeric reading, empty when the state is not a number."""
        reading = self._state_reading(entity_id)
        if reading is None or reading.missing:
            return reading
        try:
            return Reading(
                value=float(reading.value),
                updated_ago=reading.updated_ago,
                stable_for=reading.stable_for,
            )
        except (TypeError, ValueError):
            return Reading()

    def _binary(self, entity_id: str | None) -> Reading | None:
        """An on/off reading as a bool."""
        reading = self._state_reading(entity_id)
        if reading is None or reading.missing:
            return reading
        return Reading(
            value=reading.value == "on",
            updated_ago=reading.updated_ago,
            stable_for=reading.stable_for,
        )

    def _compressor(self) -> Reading:
        """Whether the heat pump is running.

        The unit reports a status rather than a boolean, and anything that is
        not off counts as running. Unknown counts as running too, in the caller:
        a lockout that errs towards leaving the release alone is the safe way
        round.
        """
        reading = self._state_reading(self.hub_config.get(CONF_COMPRESSOR_SENSOR))
        if reading is None or reading.missing:
            return Reading()
        return Reading(
            value=str(reading.value) not in ("off", "0"),
            updated_ago=reading.updated_ago,
            stable_for=reading.stable_for,
        )

    def _room_temperature(self, room: RoomRuntime) -> Reading:
        """A room's temperature, from its own sensor or from its thermostat."""
        if sensor := room.config.get(CONF_TEMPERATURE_SENSOR):
            reading = self._number(sensor)
            return reading if reading is not None else Reading()

        state = None
        if entity := room.climate_entity:
            state = self.hass.states.get(entity)
        if state is None:
            return Reading()
        value = state.attributes.get("current_temperature")
        if value is None:
            return Reading()
        try:
            value = float(value)
        except (TypeError, ValueError):
            return Reading()
        now = dt_util.utcnow()
        return Reading(value=value, updated_ago=now - state.last_updated)

    async def _forecast_max(self) -> Reading | None:
        """Today's forecast high, or None when no weather entity is configured.

        Read through the service rather than an attribute, because the forecast
        attribute was removed from weather entities.
        """
        entity = self.hub_config.get(CONF_FORECAST_ENTITY)
        if not entity:
            return None
        try:
            response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": entity, "type": "daily"},
                blocking=True,
                return_response=True,
            )
        except Exception as err:  # noqa: BLE001 - a forecast is never essential
            _LOGGER.debug("Forecast unavailable from %s: %s", entity, err)
            return Reading()

        forecast = (response or {}).get(entity, {}).get("forecast") or []
        if not forecast:
            return Reading()
        value = forecast[0].get("temperature")
        if value is None:
            return Reading()
        return Reading(value=float(value), updated_ago=timedelta(0))

    async def _gather(self) -> Inputs:
        """Everything the engine is allowed to look at, as it stands now."""
        config = self.hub_config
        rooms = tuple(
            RoomInputs(
                room_id=room.room_id,
                name=room.title,
                config=room.config,
                temperature=self._room_temperature(room),
                contacts=tuple(
                    reading
                    for entity in room.config.get(CONF_CONTACTS) or []
                    if (reading := self._binary(entity)) is not None
                ),
                humidity=self._number(room.config.get(CONF_HUMIDITY_SENSOR)),
                co2=self._number(room.config.get(CONF_CO2_SENSOR)),
                actuator=room.actuator,
            )
            for room in self.rooms.values()
        )
        return Inputs(
            now=dt_util.now(),
            outdoor=self._number(config.get(CONF_OUTDOOR_SENSOR)) or Reading(),
            forecast_max=await self._forecast_max(),
            pv_power=self._number(config.get(CONF_PV_SENSOR)),
            heat_release=self._binary(config.get(CONF_HEAT_RELEASE_SWITCH)) or Reading(),
            cool_release=self._binary(config.get(CONF_COOL_RELEASE_SWITCH)) or Reading(),
            compressor_running=self._compressor(),
            rooms=rooms,
        )

    @property
    def operation_mode(self) -> str | None:
        """What the unit's own operating mode reads, for the repair to check."""
        state_reading = self._state_reading(
            self.hub_config.get(CONF_OPERATION_MODE_SELECT)
        )
        if state_reading is None or state_reading.missing:
            return None
        return str(state_reading.value)

    ############################################################################
    # Evaluating

    async def _async_update_data(self) -> SystemDecision:
        inputs = await self._gather()
        decision, self.engine_state = evaluate(
            inputs,
            self.hub_config,
            self.engine_state,
            enabled=self.enabled,
            mode=self.mode,
            fan_request=self.fan_request,
            holiday=self.holiday,
        )
        await self._apply(decision)
        self._record(decision)
        return decision

    ############################################################################
    # Writing down what changed

    def _record(self, decision: SystemDecision) -> None:
        """Keep the decision, log what changed, and raise what needs raising."""
        self.history.append(decision)
        self._log_changes(decision)
        self._update_issues(decision)

    def _decision_entity_id(self, unique_id: str) -> str | None:
        """The decision sensor a logbook entry should hang off."""
        return er.async_get(self.hass).async_get_entity_id(
            "sensor", DOMAIN, f"{unique_id}_decision"
        )

    def _log_changes(self, decision: SystemDecision) -> None:
        """One logbook entry per changed decision, carrying its sentence."""
        # Read before logging, because logging is what replaces it.
        previous = self._signatures.get("system")
        self._log_one(
            "system",
            decision.signature,
            self.entry.title,
            decision.message,
            self._decision_entity_id(self.entry.entry_id),
        )
        if self._notable(decision, previous):
            self._queue_notification(decision.message)

        by_id = {room.room_id: room for room in self.rooms.values()}
        for room_decision in decision.rooms:
            room = by_id.get(room_decision.room_id)
            self._log_one(
                room_decision.room_id,
                room_decision.signature,
                room_decision.name,
                room_decision.message,
                None if room is None else self._decision_entity_id(room.subentry_id),
            )

    def _log_one(
        self,
        key: str,
        signature: tuple,
        name: str,
        message: str,
        entity_id: str | None,
    ) -> None:
        previous = self._signatures.get(key)
        self._signatures[key] = signature
        if previous is None or previous == signature:
            # Nothing to say on the first pass, and nothing to say when nothing
            # changed. A setpoint that drifts by a tenth is not an entry.
            return
        self.hass.bus.async_fire(
            EVENT_DECISION,
            {
                "name": name,
                "message": message,
                "entity_id": entity_id,
                "key": key,
            },
        )

    def _notable(self, decision: SystemDecision, previous: tuple | None) -> bool:
        """Whether a person should be told, as opposed to it being logged.

        A release turning over is worth a message: it is the expensive thing in
        the house starting or stopping. A fan level is not.
        """
        if previous is None:
            return False
        was_heat, was_cool, was_reason = previous[2], previous[3], previous[1]
        if (decision.heat_release, decision.cool_release) != (was_heat, was_cool):
            return True
        return str(decision.reason) != was_reason and decision.reason in (
            Reason.FROST_PROTECTION,
            Reason.OUTDOOR_UNAVAILABLE,
        )

    ############################################################################
    # Telling a person

    def _queue_notification(self, line: str) -> None:
        """Gather a line, and send what has gathered after the window."""
        if not self.hub_config.get(CONF_NOTIFY_SERVICE):
            return
        prefix = "[dry run] " if self.dry_run else ""
        self._pending.append(f"{prefix}{line}")
        if self._notify_scheduled:
            return
        self._notify_scheduled = True
        self._unsubscribe.append(
            async_call_later(
                self.hass, NOTIFY_WINDOW.total_seconds(), self._flush_notifications
            )
        )

    @callback
    def _flush_notifications(self, _now: datetime) -> None:
        self._notify_scheduled = False
        lines, self._pending = self._pending, []
        service = self.hub_config.get(CONF_NOTIFY_SERVICE)
        if not lines or not service or "." not in service:
            return
        domain, _, name = service.partition(".")
        self.hass.async_create_task(
            self.hass.services.async_call(
                domain, name, {"message": "\n".join(lines)}, blocking=False
            )
        )

    ############################################################################
    # Repairs

    def _update_issues(self, decision: SystemDecision) -> None:
        """Raise and clear the three things worth a repair entry."""
        self._issue(
            ISSUE_OPERATION_MODE,
            self.operation_mode not in (None, REQUIRED_OPERATION_MODE),
            {"mode": str(self.operation_mode)},
        )

        now = dt_util.utcnow()
        if decision.degraded:
            self._degraded_since = self._degraded_since or now
            long_enough = now - self._degraded_since >= DEGRADED_GRACE
        else:
            self._degraded_since = None
            long_enough = False
        self._issue(
            ISSUE_INPUT_UNAVAILABLE,
            long_enough,
            {"inputs": ", ".join(decision.degraded)},
        )

        self._issue(
            ISSUE_STUCK_WRITE,
            bool(self.stuck_writes),
            {"writes": ", ".join(self.stuck_writes)},
        )

    def _issue(
        self, issue_id: str, raised: bool, placeholders: dict[str, str]
    ) -> None:
        if raised:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=issue_id,
                translation_placeholders=placeholders,
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)

    ############################################################################
    # Writing

    def plan(self, decision: SystemDecision) -> list[Write]:
        """Every write that would carry this decision out, needed or not."""
        writes = schwoerer.central_writes(decision, self.hub_config)
        by_id = {room.room_id: room for room in self.rooms.values()}
        for room_decision in decision.rooms:
            room = by_id.get(room_decision.room_id)
            if room is None or not room.climate_entity:
                continue
            adapter = (
                schwoerer if room.actuator is ActuatorKind.WGT_ROOM else generic
            )
            writes.extend(adapter.room_writes(room_decision, room.climate_entity))
        return writes

    def needs_write(self, write: Write) -> bool:
        """Whether this write would change anything the device reports.

        An entity that is not reporting a comparable value answers no. Not
        knowing is not a difference, and treating it as one would rewrite every
        register on every restart.
        """
        state = self.hass.states.get(write.entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return False
        current = write.reader(state)
        if current is None:
            return False
        if isinstance(write.expect, bool) or isinstance(current, bool):
            return bool(current) != bool(write.expect)
        if isinstance(write.expect, (int, float)) and isinstance(current, (int, float)):
            return abs(float(current) - float(write.expect)) > write.tolerance
        return str(current) != str(write.expect)

    async def _apply(self, decision: SystemDecision) -> None:
        """Send what differs, paced, and keep track of what refuses to stick."""
        if not self._evaluated:
            # The first evaluation only ever publishes. The switches and selects
            # that hold the mode, holiday and the fan request restore themselves
            # after this runs, so acting now would act on defaults: a restart
            # would write the ventilation mode over whatever was really set.
            self._evaluated = True
            return

        needed = [write for write in self.plan(decision) if self.needs_write(write)]

        if not needed:
            # The steady state, and the whole point: the bus stays quiet.
            self._attempted.clear()
            self._stuck.clear()
            self._rate_limited = False
            return

        self._count_stuck(needed)

        if self.dry_run:
            for write in needed:
                _LOGGER.info(
                    "[dry run] would set %s to %s on %s",
                    write.label,
                    write.expect,
                    write.entity_id,
                )
            return

        now = dt_util.utcnow()
        if self._last_write is not None and now - self._last_write < MIN_WRITE_INTERVAL:
            # Come back when the window is open rather than waiting for the next
            # tick, which could be a quarter of an hour away.
            wait = (MIN_WRITE_INTERVAL - (now - self._last_write)).total_seconds()
            if not self._rate_limited:
                self._rate_limited = True
                self._unsubscribe.append(
                    async_call_later(self.hass, wait + 1, self._after_rate_limit)
                )
            _LOGGER.debug("Holding %d writes for %.0f s", len(needed), wait)
            return

        self._rate_limited = False
        self._last_write = now
        self._attempted = {write.label for write in needed}

        for index, write in enumerate(needed):
            if index:
                # Spaced, so a transition that touches six rooms does not arrive
                # as a burst on a bus that is also being polled.
                await asyncio.sleep(WRITE_SPACING)
            _LOGGER.debug(
                "Setting %s to %s on %s", write.label, write.expect, write.entity_id
            )
            try:
                await self.hass.services.async_call(
                    write.domain, write.service, write.service_data, blocking=True
                )
            except Exception as err:  # noqa: BLE001 - one bad write is not the lot
                _LOGGER.warning("Failed to set %s: %s", write.label, err)

    def _count_stuck(self, needed: list[Write]) -> None:
        """Count registers that were written and still do not read back.

        The first failure is not worth a word: diffing against what the device
        reports means a dropped write is retried on the next evaluation. One that
        is still wrong after several goes is a different thing.
        """
        labels = {write.label for write in needed}
        for label in labels & self._attempted:
            self._stuck[label] = self._stuck.get(label, 0) + 1
        for label in set(self._stuck) - labels:
            del self._stuck[label]

    @property
    def stuck_writes(self) -> tuple[str, ...]:
        """Labels that have refused to take their value often enough to report."""
        return tuple(
            label for label, count in sorted(self._stuck.items()) if count >= STUCK_AFTER
        )

    @callback
    def _after_rate_limit(self, _now: datetime) -> None:
        self._rate_limited = False
        self.hass.async_create_task(self.async_request_refresh())

    ############################################################################
    # Watching

    def watched_entities(self) -> list[str]:
        """Every entity whose change should cause a re-evaluation."""
        config = self.hub_config
        entities = [
            config.get(key)
            for key in (
                CONF_OUTDOOR_SENSOR,
                CONF_PV_SENSOR,
                CONF_HEAT_RELEASE_SWITCH,
                CONF_COOL_RELEASE_SWITCH,
                CONF_COMPRESSOR_SENSOR,
            )
        ]
        for room in self.rooms.values():
            entities.append(room.config.get(CONF_CLIMATE_ENTITY))
            entities.append(room.config.get(CONF_TEMPERATURE_SENSOR))
            entities.append(room.config.get(CONF_HUMIDITY_SENSOR))
            entities.append(room.config.get(CONF_CO2_SENSOR))
            entities.extend(room.config.get(CONF_CONTACTS) or [])
        return sorted({entity for entity in entities if entity})

    async def async_start_watching(self) -> None:
        """Subscribe to the inputs. The tick alone would miss a window."""
        if entities := self.watched_entities():
            self._unsubscribe.append(
                async_track_state_change_event(self.hass, entities, self._on_change)
            )

    @callback
    def _on_change(self, _event: Event[EventStateChangedData]) -> None:
        self.hass.async_create_task(self.async_request_refresh())

    async def async_shutdown(self) -> None:
        for unsubscribe in self._unsubscribe:
            unsubscribe()
        self._unsubscribe.clear()
        await super().async_shutdown()


def _subentry_title(subentry: ConfigSubentry) -> str:
    """A room's name, from its own data if it has one."""
    return subentry.data.get(CONF_NAME) or subentry.title
