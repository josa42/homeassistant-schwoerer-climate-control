"""Shared entity base classes."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClimateControlCoordinator, RoomRuntime

MANUFACTURER = "Schwörer Climate Control"


class HubEntity(CoordinatorEntity[ClimateControlCoordinator]):
    """An entity on the central device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ClimateControlCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer=MANUFACTURER,
            model="Controller",
            entry_type=DeviceEntryType.SERVICE,
        )


class RoomEntity(CoordinatorEntity[ClimateControlCoordinator]):
    """An entity on one controlled room's own device.

    The room gets a device of this integration rather than hanging off the one
    the ventilation integration made, because half the rooms are not on the unit
    at all. A bathroom heated by a relay has no device over there to hang from.
    """

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: ClimateControlCoordinator, room: RoomRuntime, key: str
    ) -> None:
        super().__init__(coordinator)
        self._subentry_id = room.subentry_id
        self._room_id = room.room_id
        self._attr_unique_id = f"{room.subentry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, room.subentry_id)},
            name=room.title,
            manufacturer=MANUFACTURER,
            model="Controlled room",
            via_device_id=coordinator.hub_device_id,
        )

    @property
    def room(self) -> RoomRuntime | None:
        """The room this entity belongs to, if it still exists."""
        return self.coordinator.rooms.get(self._subentry_id)
