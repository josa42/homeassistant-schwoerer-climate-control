"""Finding the unit's entities so the setup form arrives filled in.

Every entity of the ventilation integration publishes an ``entity_type``
attribute carrying its translation key, and room entities add a ``room_number``.
That is a stable public shape, so discovery reads attributes rather than
guessing at entity ids.

Discovery only suggests. Nothing here is required for setup to work, and a
suggestion that is wrong is corrected in the form.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_BYPASS_SENSOR,
    CONF_COMPRESSOR_SENSOR,
    CONF_COOL_RELEASE_SWITCH,
    CONF_EXTRACT_TEMPERATURE_SENSOR,
    CONF_FAN_SELECT,
    CONF_FUNCTION_SELECT,
    CONF_HEAT_RELEASE_SWITCH,
    CONF_OPERATION_MODE_SELECT,
    CONF_OUTDOOR_SENSOR,
    CONF_SUPPLY_TEMPERATURE_SENSOR,
)

#: Our configuration key against the entity_type the ventilation integration
#: publishes for it.
UNIT_ENTITY_TYPES: dict[str, str] = {
    CONF_OUTDOOR_SENSOR: "temperature_t10_outdoor",
    CONF_FAN_SELECT: "fan_speed",
    CONF_OPERATION_MODE_SELECT: "operation_mode",
    CONF_FUNCTION_SELECT: "heating_cooling_function",
    CONF_HEAT_RELEASE_SWITCH: "heat_pump_heating_enabled",
    CONF_COOL_RELEASE_SWITCH: "heat_pump_cooling_enabled",
    CONF_COMPRESSOR_SENSOR: "heat_pump_status",
    CONF_SUPPLY_TEMPERATURE_SENSOR: "temperature_t3_before_reheater",
    CONF_EXTRACT_TEMPERATURE_SENSOR: "temperature_t5_exhaust_air",
    CONF_BYPASS_SENSOR: "bypass_state",
}

ROOM_CLIMATE_TYPE = "climate_room"

#: Device name prefixes the ventilation integration puts in front of a room.
_NAME_PREFIXES = ("WGT - ", "WRT - ")

#: What a room's entity is called after its name, which a device is not.
_NAME_SUFFIXES = ("Raumthermostat", "Room thermostat", "Thermostat")


@dataclass(frozen=True, slots=True)
class DiscoveredRoom:
    """A room of the unit, as found in the state machine."""

    number: int
    name: str
    climate_entity: str


def discover_unit(hass: HomeAssistant) -> dict[str, str]:
    """The unit's central entities, keyed by our own configuration keys."""
    wanted = {value: key for key, value in UNIT_ENTITY_TYPES.items()}
    found: dict[str, str] = {}
    for state in hass.states.async_all():
        entity_type = state.attributes.get("entity_type")
        if entity_type in wanted and state.attributes.get("room_number") is None:
            found[wanted[entity_type]] = state.entity_id
    return found


def discover_rooms(hass: HomeAssistant) -> list[DiscoveredRoom]:
    """Every room of the unit that has a thermostat, in room order."""
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    rooms: list[DiscoveredRoom] = []

    for state in hass.states.async_all("climate"):
        if state.attributes.get("entity_type") != ROOM_CLIMATE_TYPE:
            continue
        number = state.attributes.get("room_number")
        if number is None:
            continue
        rooms.append(
            DiscoveredRoom(
                number=int(number),
                name=_room_name(hass, entities, devices, state.entity_id, int(number)),
                climate_entity=state.entity_id,
            )
        )

    return sorted(rooms, key=lambda room: room.number)


def _clean(name: str) -> str:
    """A room's name without what the ventilation integration wraps it in."""
    for prefix in _NAME_PREFIXES:
        name = name.removeprefix(prefix)
    for suffix in _NAME_SUFFIXES:
        name = name.removesuffix(suffix).removesuffix(suffix.lower())
    return name.strip()


def _room_name(
    hass: HomeAssistant,
    entities: er.EntityRegistry,
    devices: dr.DeviceRegistry,
    entity_id: str,
    number: int,
) -> str:
    """What the room is called, preferring what the user named its device.

    The friendly name is the fallback and needs more taken off it: a device is
    called "WGT - Wohnzimmer" while its thermostat is called "WGT - Wohnzimmer
    Raumthermostat", and neither spelling is what the room is called.
    """
    entry = entities.async_get(entity_id)
    if entry is not None and entry.device_id:
        device = devices.async_get(entry.device_id)
        if device is not None and (name := _clean(device.name_by_user or device.name or "")):
            return name

    state = hass.states.get(entity_id)
    if state is not None and (friendly := state.attributes.get("friendly_name")):
        if name := _clean(str(friendly)):
            return name
    return f"Room {number}"
