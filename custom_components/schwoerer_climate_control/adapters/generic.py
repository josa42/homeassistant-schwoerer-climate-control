"""Any other climate entity: a radiator valve, or a thermostat before a relay.

This adapter knows one thing, which is that such an entity regulates its own
room. The controller gives it a setpoint and says whether it may run; hysteresis,
minimum run time and minimum rest are its own business, and in the case of a
generic_thermostat they are already solved there.
"""

from __future__ import annotations

from homeassistant.components.climate.const import HVACMode

from ..models import RoomDecision
from . import Write, hvac_mode_write, temperature_write


def room_writes(room: RoomDecision, climate_entity: str) -> list[Write]:
    """The writes for one room the unit does not heat."""
    writes: list[Write] = []

    if room.target_temperature is not None:
        writes.append(
            temperature_write(
                f"{room.room_id}.target", climate_entity, room.target_temperature
            )
        )

    if room.heating_enabled is not None:
        writes.append(
            hvac_mode_write(
                f"{room.room_id}.heating",
                climate_entity,
                HVACMode.HEAT if room.heating_enabled else HVACMode.OFF,
            )
        )

    return writes
