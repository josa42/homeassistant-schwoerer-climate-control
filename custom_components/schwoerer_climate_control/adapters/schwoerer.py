"""The Schwörer WGT, as spoken to through the schwoerer_lueftung entities.

Everything peculiar to this unit lives here: that the fan level is one select
for the whole house, that heating and cooling are two release switches, that
register 230 has to read cooling for the bypass damper to open at all, and that
a room thermostat's hvac mode is its auxiliary heater rather than an on and off.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate.const import HVACMode

from ..const import (
    CONF_COOL_RELEASE_SWITCH,
    CONF_FAN_SELECT,
    CONF_FUNCTION_SELECT,
    CONF_HEAT_RELEASE_SWITCH,
)
from ..models import RoomDecision, SystemDecision
from . import Write, hvac_mode_write, select_write, switch_write, temperature_write


def central_writes(decision: SystemDecision, config: dict[str, Any]) -> list[Write]:
    """The writes that carry a system decision to the unit.

    A field left as None in the decision produces no write. That is how the
    compressor lockout and a disabled controller express themselves: there is
    nothing to send, rather than a value that happens to match.
    """
    writes: list[Write] = []

    if decision.fan_level is not None and (entity := config.get(CONF_FAN_SELECT)):
        writes.append(select_write("fan_level", entity, str(decision.fan_level)))

    if decision.heat_release is not None and (
        entity := config.get(CONF_HEAT_RELEASE_SWITCH)
    ):
        writes.append(switch_write("heat_release", entity, decision.heat_release))

    if decision.cool_release is not None and (
        entity := config.get(CONF_COOL_RELEASE_SWITCH)
    ):
        writes.append(switch_write("cool_release", entity, decision.cool_release))

    if decision.heating_cooling_function is not None and (
        entity := config.get(CONF_FUNCTION_SELECT)
    ):
        writes.append(
            select_write(
                "heating_cooling_function",
                entity,
                str(decision.heating_cooling_function),
            )
        )

    return writes


def room_writes(room: RoomDecision, climate_entity: str) -> list[Write]:
    """The writes for one room of the unit."""
    writes: list[Write] = []

    if room.target_temperature is not None:
        writes.append(
            temperature_write(
                f"{room.room_id}.target", climate_entity, room.target_temperature
            )
        )

    if room.auxiliary_heat is not None:
        # The thermostat has no off: fan_only is a room that is ventilated but
        # not heated by its own second stage.
        writes.append(
            hvac_mode_write(
                f"{room.room_id}.auxiliary_heat",
                climate_entity,
                HVACMode.HEAT if room.auxiliary_heat else HVACMode.FAN_ONLY,
            )
        )

    return writes
