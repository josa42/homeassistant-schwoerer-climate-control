"""The selects: which direction of energy is allowed, and how the fan runs."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_FAN_NIGHT, FAN_MAX, FAN_MIN, FanMode, Mode
from .coordinator import ClimateControlConfigEntry, ClimateControlCoordinator
from .entity import HubEntity

#: The fan modes and the fixed stages in one list, the way the unit's own fan
#: select is built. Two separate controls could contradict each other.
STAGES: list[str] = [str(stage) for stage in range(FAN_MIN, FAN_MAX + 1)]
FAN_OPTIONS: list[str] = [mode.value for mode in FanMode] + STAGES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ClimateControlConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [ModeSelect(coordinator), FanSelect(coordinator), FanNightSelect(coordinator)]
    )


class ModeSelect(HubEntity, SelectEntity, RestoreEntity):
    """Heating, ventilation or cooling.

    Named after the direction of energy rather than the season, so that each rule
    reads the gate it cares about and deriving this automatically later changes
    only where it comes from.
    """

    _attr_options = [mode.value for mode in Mode]

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, "mode")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in self._attr_options:
            await self.coordinator.async_set_mode(Mode(last.state))

    @property
    def current_option(self) -> str:
        return self.coordinator.mode.value

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_mode(Mode(option))
        self.async_write_ha_state()


class FanSelect(HubEntity, SelectEntity, RestoreEntity):
    """How the fan level is chosen, or the stage it is pinned to."""

    _attr_options = FAN_OPTIONS

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, "fan")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in FAN_OPTIONS:
            await self.coordinator.async_set_fan_request(_parse(last.state))

    @property
    def current_option(self) -> str:
        request = self.coordinator.fan_request
        return request.value if isinstance(request, FanMode) else str(request)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_fan_request(_parse(option))
        self.async_write_ha_state()


class FanNightSelect(HubEntity, SelectEntity, RestoreEntity):
    """The fan stage at night, which the night setback switch leaves alone.

    Starts from the configured stage the first time it exists, and holds its own
    value from then on.
    """

    _attr_options = STAGES

    def __init__(self, coordinator: ClimateControlCoordinator) -> None:
        super().__init__(coordinator, CONF_FAN_NIGHT)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        option = last.state if last is not None and last.state in STAGES else None
        if option is None:
            option = str(int(self.coordinator.setting(CONF_FAN_NIGHT)))
        await self.coordinator.async_set_hub_setting(
            CONF_FAN_NIGHT, int(option), restoring=True
        )

    @property
    def current_option(self) -> str | None:
        stage = self.coordinator.hub_settings.get(CONF_FAN_NIGHT)
        return None if stage is None else str(stage)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_hub_setting(CONF_FAN_NIGHT, int(option))
        self.async_write_ha_state()


def _parse(option: str) -> FanMode | int:
    """A mode, or a fixed stage."""
    try:
        return FanMode(option)
    except ValueError:
        return int(option)
