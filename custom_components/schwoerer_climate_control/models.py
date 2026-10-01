"""Configuration resolution, sensor readings and the decision records.

The decision record is the whole point of the transparency requirement: every
evaluation produces immutable objects carrying the inputs that were read, the
gates that were applied, the settings that were used and where each of them
came from. Nothing may write a register without producing one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .const import (
    DEFAULTS,
    OVERRIDABLE,
    FanReason,
    HeatingCoolingFunction,
    Intent,
    Mode,
    Reason,
    RoomIntent,
    RoomReason,
)


@dataclass(frozen=True, slots=True)
class Setting:
    """A resolved setting plus where it came from."""

    value: Any
    source: str  # "room" | "hub" | "default"

    def as_dict(self) -> dict[str, Any]:
        return {"value": self.value, "source": self.source}


class EffectiveConfig:
    """Resolves hub settings against per-room overrides.

    Keeping the source next to the value is what lets a decision explain why a
    setpoint was 18.5 and not 20 without the reader opening two dialogs and
    diffing them.
    """

    def __init__(self, hub: dict[str, Any], room: dict[str, Any] | None = None) -> None:
        self._hub = hub
        self._room = room or {}

    def resolve(self, key: str) -> Setting:
        """Resolve one key, room first."""
        if self._room.get(key) is not None:
            return Setting(self._room[key], "room")
        if self._hub.get(key) is not None:
            return Setting(self._hub[key], "hub")
        return Setting(DEFAULTS.get(key), "default")

    def get(self, key: str) -> Any:
        """Resolve a key and return just the value."""
        return self.resolve(key).value

    def number(self, key: str) -> float:
        """Resolve a key that must be a number."""
        return float(self.get(key))

    def snapshot(self, keys: tuple[str, ...] = OVERRIDABLE) -> dict[str, dict[str, Any]]:
        """Every resolvable setting with its value and source, for the record."""
        return {key: self.resolve(key).as_dict() for key in keys}


@dataclass(frozen=True, slots=True)
class Reading:
    """One sensor value, or the documented absence of one.

    A missing reading is a first-class value rather than a skipped branch. v1
    did ``if not state: continue`` everywhere, which made a dead CO₂ sensor mean
    good air and a dead contact mean a closed window, both silently.
    """

    value: Any = None
    #: How long ago the source last wrote the value. ``None`` when it has never
    #: reported at all.
    updated_ago: timedelta | None = None
    #: How long the value has been what it is. Only the contacts use it, where
    #: the question is not the age of the number but how long the window has
    #: been open.
    stable_for: timedelta | None = None

    @property
    def missing(self) -> bool:
        """Nothing usable was read."""
        return self.value is None

    def stale(self, max_age: timedelta) -> bool:
        """Older than this interface is willing to trust."""
        if self.missing:
            return True
        return self.updated_ago is None or self.updated_ago > max_age

    def as_number(self) -> float | None:
        """The value as a float, or None when it is not one."""
        try:
            return None if self.missing else float(self.value)
        except (TypeError, ValueError):
            return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "age": None if self.updated_ago is None else self.updated_ago.total_seconds(),
            "stable_for": (
                None if self.stable_for is None else self.stable_for.total_seconds()
            ),
            "ok": not self.missing,
        }


@dataclass(frozen=True, slots=True)
class Gate:
    """One condition that was evaluated, and what it concluded."""

    name: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class RoomDecision:
    """One complete evaluation of one room."""

    room_id: str
    name: str
    intent: RoomIntent
    reason: RoomReason
    message: str
    #: What the room's climate entity should be set to. ``None`` means the room
    #: is not to be written at all, which is not the same as a setpoint of 0.
    target_temperature: float | None = None
    #: Whether the room's auxiliary heater should run. ``None`` for a room that
    #: has none, so that "off" is never written to something that cannot heat.
    auxiliary_heat: bool | None = None
    window_open: bool = False
    gates: tuple[Gate, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: Inputs that were configured but could not be read.
    degraded: tuple[str, ...] = ()

    def gate_passed(self, name: str) -> bool | None:
        """Whether one gate held, or None if it was never reached."""
        for gate in self.gates:
            if gate.name == name:
                return gate.passed
        return None

    def as_attributes(self) -> dict[str, Any]:
        """Compact, flat form for the sensor.

        The recorder writes this on every state change, so the full trace lives
        in diagnostics instead.
        """
        return {
            "reason_code": str(self.reason),
            "message": self.message,
            "target_temperature": self.target_temperature,
            "auxiliary_heat": self.auxiliary_heat,
            "window_open": self.window_open,
            "room_temperature": self.inputs.get("temperature", {}).get("value"),
            "degraded": list(self.degraded),
        }

    def as_dict(self) -> dict[str, Any]:
        """Full record for diagnostics."""
        return {
            "room_id": self.room_id,
            "name": self.name,
            "intent": str(self.intent),
            "reason_code": str(self.reason),
            "message": self.message,
            "target_temperature": self.target_temperature,
            "auxiliary_heat": self.auxiliary_heat,
            "window_open": self.window_open,
            "gates": [gate.as_dict() for gate in self.gates],
            "inputs": self.inputs,
            "settings": self.settings,
            "degraded": list(self.degraded),
        }


@dataclass(frozen=True, slots=True)
class SystemDecision:
    """One complete evaluation of the unit, plus every room."""

    timestamp: datetime
    intent: Intent
    reason: Reason
    message: str
    #: The mode that was acted on. Differs from the one that was asked for when
    #: an input was missing and ventilation took over.
    mode: Mode
    requested_mode: Mode
    holiday: bool = False
    #: ``None`` on any of these means "do not write this register". For the
    #: releases that is how the compressor lockout expresses itself: the value
    #: it would want is in the message, and nothing is sent.
    heat_release: bool | None = None
    cool_release: bool | None = None
    heating_cooling_function: HeatingCoolingFunction | None = None
    fan_level: int | None = None
    fan_reason: FanReason | None = None
    #: The room that asked for the fan level, when one did.
    fan_requested_by: str | None = None
    #: Set when the fan mode held the level below what the rules asked for.
    fan_capped_from: int | None = None
    is_night: bool = False
    rooms: tuple[RoomDecision, ...] = ()
    gates: tuple[Gate, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, dict[str, Any]] = field(default_factory=dict)
    degraded: tuple[str, ...] = ()

    def gate_passed(self, name: str) -> bool | None:
        """Whether one gate held, or None if it was never reached."""
        for gate in self.gates:
            if gate.name == name:
                return gate.passed
        return None

    def as_attributes(self) -> dict[str, Any]:
        """Compact, flat form for the sensor."""
        return {
            "reason_code": str(self.reason),
            "message": self.message,
            "mode": str(self.mode),
            # Both, because they disagree exactly when something is wrong, and a
            # reader who only saw one of them would call that a bug.
            "requested_mode": str(self.requested_mode),
            "holiday": self.holiday,
            "heat_release": self.heat_release,
            "cool_release": self.cool_release,
            "fan_level": self.fan_level,
            "fan_reason": None if self.fan_reason is None else str(self.fan_reason),
            "fan_requested_by": self.fan_requested_by,
            "fan_capped_from": self.fan_capped_from,
            "is_night": self.is_night,
            "outdoor_temperature": self.inputs.get("outdoor", {}).get("value"),
            "degraded": list(self.degraded),
        }

    def as_dict(self) -> dict[str, Any]:
        """Full record for diagnostics."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "intent": str(self.intent),
            "reason_code": str(self.reason),
            "message": self.message,
            "mode": str(self.mode),
            "requested_mode": str(self.requested_mode),
            "holiday": self.holiday,
            "heat_release": self.heat_release,
            "cool_release": self.cool_release,
            "heating_cooling_function": (
                None
                if self.heating_cooling_function is None
                else str(self.heating_cooling_function)
            ),
            "fan_level": self.fan_level,
            "fan_reason": None if self.fan_reason is None else str(self.fan_reason),
            "fan_requested_by": self.fan_requested_by,
            "fan_capped_from": self.fan_capped_from,
            "is_night": self.is_night,
            "gates": [gate.as_dict() for gate in self.gates],
            "inputs": self.inputs,
            "settings": self.settings,
            "degraded": list(self.degraded),
            "rooms": [room.as_dict() for room in self.rooms],
        }
