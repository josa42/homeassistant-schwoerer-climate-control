"""The Schwörer Climate Control integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_SURPLUS_ENTITY,
    CONF_SURPLUS_START,
    CONF_SURPLUS_TARGET_BOOST,
    DOMAIN,
)
from .coordinator import ClimateControlConfigEntry, ClimateControlCoordinator

_LOGGER = logging.getLogger(__name__)

# There is nothing to configure in YAML; everything lives in config entries.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

STRATEGY_FILENAME = "schwoerer-climate-control-dashboard.js"
STRATEGY_URL_PATH = f"/{DOMAIN}/{STRATEGY_FILENAME}"
#: Kept in step with the manifest by the release script, and served as a query
#: string, so a browser does not keep running the strategy it cached before an
#: upgrade.
STRATEGY_VERSION = "0.1.0"

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the dashboard strategy. Called once per Home Assistant session."""
    http = getattr(hass, "http", None)
    if http is None:
        return True

    strategy = Path(__file__).parent / "www" / STRATEGY_FILENAME
    if not strategy.is_file():
        _LOGGER.warning("Dashboard strategy asset missing at %s", strategy)
        return True

    try:
        await http.async_register_static_paths(
            [StaticPathConfig(STRATEGY_URL_PATH, str(strategy), cache_headers=False)]
        )
        add_extra_js_url(hass, f"{STRATEGY_URL_PATH}?v={STRATEGY_VERSION}")
    except Exception as err:  # noqa: BLE001
        # A dashboard is convenience. Whatever goes wrong here, the controller
        # still has to run, so this can never abort the setup.
        _LOGGER.warning("Could not register the dashboard strategy: %s", err)
    return True


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


async def async_migrate_entry(
    hass: HomeAssistant, entry: ClimateControlConfigEntry
) -> bool:
    """Carry an older entry forward.

    Version 2 replaced the PV fields with one surplus input used for both cooling
    and raising setpoints. Silently dropping the old configuration would turn the
    setpoint boost off without saying so, which is exactly the kind of quiet
    breakage this integration exists to avoid.
    """
    if entry.version >= 2:
        return True

    renamed = {
        "pv_sensor": CONF_SURPLUS_ENTITY,
        "pv_surplus_above": CONF_SURPLUS_START,
        "pv_target_boost": CONF_SURPLUS_TARGET_BOOST,
    }
    data = dict(entry.data)
    options = dict(entry.options)
    for was, now in renamed.items():
        for store in (data, options):
            if was in store:
                store.setdefault(now, store.pop(was))

    hass.config_entries.async_update_entry(
        entry, data=data, options=options, version=2
    )
    _LOGGER.info("Migrated the PV fields to one surplus input")
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
