"""The three switches that say what the controller may do."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .coordinator import ClimateControlConfigEntry, ClimateControlCoordinator
from .entity import HubEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [ActiveSwitch(coordinator), HolidaySwitch(coordinator), DryRunSwitch(coordinator)]
    )


class ActiveSwitch(HubEntity, SwitchEntity, RestoreEntity):
    """Off means no register is written at all.

    The unit keeps running on its last values and the decision sensors keep
    showing what the controller would do, which is what makes this the switch to
    reach for while working out why it did something.
    """

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, "active")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            await self.coordinator.async_set_enabled(last.state == STATE_ON)

    @property
    def is_on(self) -> bool:
        return self.coordinator.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_enabled(False)
        self.async_write_ha_state()


class HolidaySwitch(HubEntity, SwitchEntity, RestoreEntity):
    """A modifier on the mode, not a mode of its own."""

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, "holiday")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            await self.coordinator.async_set_holiday(last.state == STATE_ON)

    @property
    def is_on(self) -> bool:
        return self.coordinator.holiday

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_holiday(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_holiday(False)
        self.async_write_ha_state()


class DryRunSwitch(HubEntity, SwitchEntity, RestoreEntity):
    """Everything is decided and published, nothing is sent."""

    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, "dry_run")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            await self.coordinator.async_set_dry_run(last.state == STATE_ON)

    @property
    def is_on(self) -> bool:
        return self.coordinator.dry_run

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_dry_run(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_dry_run(False)
        self.async_write_ha_state()
