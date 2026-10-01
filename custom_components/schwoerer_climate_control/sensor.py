"""The decision sensors, one for the unit and one for each room.

The state is the intent in a word. The attributes are the rest of the answer:
the inputs with their age, the gates with their outcome, the settings with where
each came from, and a sentence a person can read. The three that change shape on
every evaluation are kept out of the recorder, and the history lives in the
logbook instead.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import SUBENTRY_TYPE_ROOM, Intent, RoomIntent
from .coordinator import (
    ClimateControlConfigEntry,
    ClimateControlCoordinator,
    RoomRuntime,
)
from .entity import HubEntity, RoomEntity
from .models import UNRECORDED_ATTRIBUTES, RoomDecision


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([SystemDecisionSensor(coordinator)])

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
