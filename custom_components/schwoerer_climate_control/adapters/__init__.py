"""Turning a decision into writes, without deciding anything.

An adapter knows how one kind of device is spoken to. It never decides what
should happen: it is handed a decision and reports the writes that would carry
it out, each one carrying the value the entity should report afterwards.

That last part is what makes the diff work. The coordinator compares the
expected value against what the device currently reports, not against what it
believes it sent, so a write that does not arrive is simply attempted again next
time, and one that never arrives can be counted.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import State

from ..const import TARGET_RESOLUTION


@dataclass(frozen=True, slots=True)
class Write:
    """One intended change, and how to tell whether it is needed."""

    #: Names the thing being set, for the log line and the stuck counter.
    label: str
    entity_id: str
    #: What the entity should report once this has landed.
    expect: Any
    #: Reads the comparable value off the entity's current state.
    reader: Callable[[State], Any]
    domain: str
    service: str
    data: dict[str, Any] = field(default_factory=dict)
    #: Numbers are compared with a tolerance, because a device that stores a
    #: tenth never reports back the float that was sent.
    tolerance: float = 0.0

    @property
    def service_data(self) -> dict[str, Any]:
        return {ATTR_ENTITY_ID: self.entity_id, **self.data}


def read_switch(state: State) -> bool | None:
    """A switch as a bool, or None when it is not saying."""
    if state.state == STATE_ON:
        return True
    if state.state == STATE_OFF:
        return False
    return None


def read_option(state: State) -> str | None:
    """A select's option, or None when it has none."""
    if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return None
    return state.state


def read_hvac_mode(state: State) -> str | None:
    """A climate entity's mode, which is also its state."""
    return read_option(state)


def read_target_temperature(state: State) -> float | None:
    """A climate entity's setpoint, or None when it has not reported one."""
    value = state.attributes.get(ATTR_TEMPERATURE)
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def switch_write(label: str, entity_id: str, expect: bool) -> Write:
    """Set a switch, by the service that gets it there."""
    return Write(
        label=label,
        entity_id=entity_id,
        expect=expect,
        reader=read_switch,
        domain="switch",
        service="turn_on" if expect else "turn_off",
    )


def select_write(label: str, entity_id: str, expect: str) -> Write:
    """Choose a select's option."""
    return Write(
        label=label,
        entity_id=entity_id,
        expect=expect,
        reader=read_option,
        domain="select",
        service="select_option",
        data={"option": expect},
    )


def temperature_write(label: str, entity_id: str, expect: float) -> Write:
    """Set a climate entity's target temperature."""
    return Write(
        label=label,
        entity_id=entity_id,
        expect=expect,
        reader=read_target_temperature,
        domain="climate",
        service="set_temperature",
        data={ATTR_TEMPERATURE: expect},
        # Half the resolution the device stores: anything closer than that is
        # the same setpoint and must not be written again.
        tolerance=TARGET_RESOLUTION / 2,
    )


def hvac_mode_write(label: str, entity_id: str, expect: str) -> Write:
    """Set a climate entity's mode."""
    return Write(
        label=label,
        entity_id=entity_id,
        expect=expect,
        reader=read_hvac_mode,
        domain="climate",
        service="set_hvac_mode",
        data={"hvac_mode": expect},
    )
