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
    CONF_EXTRACT_TEMPERATURE_SENSOR,
    CONF_OUTDOOR_SENSOR,
    CONF_SUPPLY_TEMPERATURE_SENSOR,
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
        return {
            **decision.as_attributes(),
            "gates": [gate.as_dict() for gate in decision.gates],
            "inputs": decision.inputs,
            "settings": decision.settings,
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
        return {
            **decision.as_attributes(),
            "gates": [gate.as_dict() for gate in decision.gates],
            "inputs": decision.inputs,
            "settings": decision.settings,
        }


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
