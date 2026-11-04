"""The decision sensors, one for the unit and one for each room.

The state is the intent in a word. The attributes are the rest of the answer:
the inputs with their age, the gates with their outcome, the settings with where
each came from, and a sentence a person can read. The three that change shape on
every evaluation are kept out of the recorder, and the history lives in the
logbook instead.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_AUX_HOUSE_SWITCH,
    CONF_BYPASS_SENSOR,
    CONF_CO2_SENSOR,
    CONF_COMPRESSOR_SENSOR,
    CONF_CONTACTS,
    CONF_COOL_RELEASE_SWITCH,
    CONF_EXTRACT_TEMPERATURE_SENSOR,
    CONF_FAN_SELECT,
    CONF_FORECAST_ENTITY,
    CONF_FUNCTION_SELECT,
    CONF_HEAT_RELEASE_SWITCH,
    CONF_HUMIDITY_SENSOR,
    CONF_OPERATION_MODE_SELECT,
    CONF_OUTDOOR_SENSOR,
    CONF_POWER_SENSOR,
    CONF_SUPPLY_AIR_SENSOR,
    CONF_SUPPLY_TEMPERATURE_SENSOR,
    CONF_SURPLUS_ENTITY,
    CONF_TEMPERATURE_SENSOR,
    SUBENTRY_TYPE_ROOM,
    Intent,
    RoomIntent,
)
from .coordinator import (
    ClimateControlConfigEntry,
    ClimateControlCoordinator,
    RoomRuntime,
)
from .entity import HubEntity, RoomEntity
from .models import UNRECORDED_ATTRIBUTES, RoomDecision
from .recovery import Recovery, measure


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [SystemDecisionSensor(coordinator)]

    # The bypass can only be watched, and only when all three temperatures are
    # configured. Without them there is nothing to say about it, and a sensor
    # that is always unknown says something it does not mean.
    config = coordinator.hub_config
    if all(
        config.get(key)
        for key in (
            CONF_SUPPLY_TEMPERATURE_SENSOR,
            CONF_EXTRACT_TEMPERATURE_SENSOR,
            CONF_OUTDOOR_SENSOR,
        )
    ):
        entities.append(HeatRecoverySensor(coordinator))
    async_add_entities(entities)

    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        room = coordinator.rooms.get(subentry_id)
        if room is None:
            continue
        async_add_entities(
            [RoomDecisionSensor(coordinator, room)], config_subentry_id=subentry_id
        )


#: The unit's inputs a dashboard may want to read for itself, by the name it
#: knows them under.
HUB_SOURCES: dict[str, str] = {
    "outdoor": CONF_OUTDOOR_SENSOR,
    "supply_air": CONF_SUPPLY_AIR_SENSOR,
    "supply_temperature": CONF_SUPPLY_TEMPERATURE_SENSOR,
    "extract": CONF_EXTRACT_TEMPERATURE_SENSOR,
    "compressor": CONF_COMPRESSOR_SENSOR,
    "fan": CONF_FAN_SELECT,
    "heat_release": CONF_HEAT_RELEASE_SWITCH,
    "cool_release": CONF_COOL_RELEASE_SWITCH,
    "function": CONF_FUNCTION_SELECT,
    "aux_house": CONF_AUX_HOUSE_SWITCH,
    "operation_mode": CONF_OPERATION_MODE_SELECT,
    "bypass": CONF_BYPASS_SENSOR,
    "forecast": CONF_FORECAST_ENTITY,
    "surplus": CONF_SURPLUS_ENTITY,
    "power": CONF_POWER_SENSOR,
}


class SystemDecisionSensor(HubEntity, SensorEntity):
    """What the controller decided for the unit, and why."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [intent.value for intent in Intent]
    _unrecorded_attributes = frozenset(UNRECORDED_ATTRIBUTES)

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, "decision")

    @property
    def native_value(self) -> str | None:
        decision = self.coordinator.data
        return None if decision is None else decision.intent.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        decision = self.coordinator.data
        if decision is None:
            return {}
        config = self.coordinator.hub_config
        return {
            **decision.as_attributes(),
            "gates": [gate.as_dict() for gate in decision.gates],
            "thresholds": [threshold.as_dict() for threshold in decision.thresholds],
            "upcoming": [event.as_dict() for event in decision.upcoming],
            "inputs": decision.inputs,
            "settings": decision.settings,
            "sources": {
                name: config[key] for name, key in HUB_SOURCES.items() if config.get(key)
            },
        }


class RoomDecisionSensor(RoomEntity, SensorEntity):
    """What the controller decided for one room, and why."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [intent.value for intent in RoomIntent]
    _unrecorded_attributes = frozenset(UNRECORDED_ATTRIBUTES)

    def __init__(
        self, coordinator: ClimateControlCoordinator, room: RoomRuntime
    ) -> None:
        super().__init__(coordinator, room, "decision")

    @property
    def _decision(self) -> RoomDecision | None:
        decision = self.coordinator.data
        if decision is None:
            return None
        return next(
            (room for room in decision.rooms if room.room_id == self._room_id), None
        )

    @property
    def native_value(self) -> str | None:
        decision = self._decision
        return None if decision is None else decision.intent.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        decision = self._decision
        if decision is None:
            return {}
        room = self.room
        return {
            **decision.as_attributes(),
            "gates": [gate.as_dict() for gate in decision.gates],
            "thresholds": [threshold.as_dict() for threshold in decision.thresholds],
            "upcoming": [event.as_dict() for event in decision.upcoming],
            "inputs": decision.inputs,
            "settings": decision.settings,
            "sources": {} if room is None else _room_sources(room),
        }


def _room_sources(room: RoomRuntime) -> dict[str, Any]:
    """A room's own inputs, by the name a dashboard knows them under."""
    config = room.config
    sources: dict[str, Any] = {
        "climate": room.climate_entity,
        "temperature": config.get(CONF_TEMPERATURE_SENSOR) or room.climate_entity,
        "humidity": config.get(CONF_HUMIDITY_SENSOR),
        "co2": config.get(CONF_CO2_SENSOR),
        "contacts": list(config.get(CONF_CONTACTS) or []),
    }
    return {name: value for name, value in sources.items() if value}


class HeatRecoverySensor(HubEntity, SensorEntity):
    """How much heat the exchanger recovers, which is how the bypass is judged.

    The damper cannot be commanded, so this is the controller's whole part in it:
    report what the air is doing. Open and recovering fully means the air is going
    through the core either way, and that is a fault in the bypass path rather
    than anything the controller did or failed to do.
    """

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, "heat_recovery")

    def _measure(self) -> Recovery:
        config = self.coordinator.hub_config
        read = self.coordinator.number_value
        return measure(
            read(config.get(CONF_SUPPLY_TEMPERATURE_SENSOR)),
            read(config.get(CONF_EXTRACT_TEMPERATURE_SENSOR)),
            read(config.get(CONF_OUTDOOR_SENSOR)),
            self.coordinator.bypass_open,
        )

    @property
    def native_value(self) -> float | None:
        recovery = self._measure()
        return None if recovery.ratio is None else round(recovery.ratio * 100, 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        recovery = self._measure()
        return {
            "gradient": recovery.gradient,
            "meaningful": recovery.meaningful,
            "bypass_open": recovery.bypass_open,
            "bypass_effective": recovery.effective,
        }
