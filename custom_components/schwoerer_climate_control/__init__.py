"""The Schwörer Climate Control integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import ClimateControlConfigEntry, ClimateControlCoordinator

# There is nothing to configure in YAML; everything lives in config entries.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ClimateControlConfigEntry
) -> bool:
    """Set up the controller from a config entry."""
    coordinator = ClimateControlCoordinator(hass, entry)
    coordinator.load_rooms()
    coordinator.register_hub_device()
    entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_start_watching()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ClimateControlConfigEntry
) -> bool:
    """Unload the entry and stop watching."""
    await entry.runtime_data.async_shutdown()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: ClimateControlConfigEntry) -> None:
    """Reload when the configuration or a room changes."""
    await hass.config_entries.async_reload(entry.entry_id)
