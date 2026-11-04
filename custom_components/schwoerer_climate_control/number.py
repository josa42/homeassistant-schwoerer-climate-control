"""Each room's setpoints, by day and at night.

They are entities rather than options so that an automation can set them and
the history shows when they changed. A room starts from what its configuration
resolved to, and holds its own value from then on.
"""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_TARGET_NIGHT,
    CONF_TARGET_NORMAL,
    SUBENTRY_TYPE_ROOM,
    TARGET_MAX,
    TARGET_MIN,
)
from .coordinator import (
    ClimateControlConfigEntry,
    ClimateControlCoordinator,
    RoomRuntime,
)
from .entity import RoomEntity

#: The settings a room has as entities. Everything else stays in its options.
ROOM_NUMBERS: tuple[str, ...] = (CONF_TARGET_NORMAL, CONF_TARGET_NIGHT)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type != SUBENTRY_TYPE_ROOM:
            continue
        room = coordinator.rooms.get(subentry_id)
        if room is None:
            continue
        async_add_entities(
            [RoomSettingNumber(coordinator, room, key) for key in ROOM_NUMBERS],
            config_subentry_id=subentry_id,
        )


class RoomSettingNumber(RoomEntity, RestoreNumber):
    """One setpoint of one room."""

    _attr_native_min_value = TARGET_MIN
    _attr_native_max_value = TARGET_MAX
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.BOX

    def __init__(
        self, coordinator: ClimateControlCoordinator, room: RoomRuntime, key: str
    ) -> None:
        super().__init__(coordinator, room, key)
        self._key = key

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        value = last.native_value if last is not None else None
        if value is None:
            value = float(self.coordinator.setting(self._key, self.room))
        await self.coordinator.async_set_room_setting(
            self._room_id, self._key, value, restoring=True
        )

    @property
    def native_value(self) -> float | None:
        return self.coordinator.room_settings.get(self._room_id, {}).get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_setting(self._room_id, self._key, value)
        self.async_write_ha_state()
