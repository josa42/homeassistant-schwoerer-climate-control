"""Shared fixtures: a configured controller over a faked unit."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.schwoerer_climate_control.const import (
    CONF_ACTUATOR,
    CONF_CLIMATE_ENTITY,
    CONF_COMPRESSOR_SENSOR,
    CONF_CONTACTS,
    CONF_COOL_RELEASE_SWITCH,
    CONF_DRY_RUN,
    CONF_FAN_SELECT,
    CONF_FUNCTION_SELECT,
    CONF_HEAT_RELEASE_SWITCH,
    CONF_NAME,
    CONF_OPERATION_MODE_SELECT,
    CONF_OUTDOOR_SENSOR,
    DOMAIN,
    SUBENTRY_TYPE_ROOM,
    ActuatorKind,
)

pytest_plugins = "pytest_homeassistant_custom_component"

OUTDOOR = "sensor.outdoor"
FAN = "select.fan"
HEAT = "switch.heat_release"
COOL = "switch.cool_release"
FUNCTION = "select.function"
COMPRESSOR = "sensor.compressor"
OPERATION_MODE = "select.operation_mode"
THERMOSTAT = "climate.wohnzimmer"
CONTACT = "binary_sensor.wohnzimmer_window"

HUB_DATA: dict[str, Any] = {
    CONF_OUTDOOR_SENSOR: OUTDOOR,
    CONF_FAN_SELECT: FAN,
    CONF_HEAT_RELEASE_SWITCH: HEAT,
    CONF_COOL_RELEASE_SWITCH: COOL,
    CONF_FUNCTION_SELECT: FUNCTION,
    CONF_COMPRESSOR_SENSOR: COMPRESSOR,
    CONF_OPERATION_MODE_SELECT: OPERATION_MODE,
    CONF_DRY_RUN: False,
}

ROOM_DATA: dict[str, Any] = {
    CONF_NAME: "Wohnzimmer",
    CONF_ACTUATOR: ActuatorKind.WGT_ROOM.value,
    CONF_CLIMATE_ENTITY: THERMOSTAT,
    CONF_CONTACTS: [CONTACT],
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make the custom integration loadable in every test."""
    return


@pytest.fixture(autouse=True)
def no_write_spacing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Writes are paced in production; waiting a second per write is not a test."""
    monkeypatch.setattr(
        "custom_components.schwoerer_climate_control.coordinator.WRITE_SPACING", 0
    )


WRITE_SERVICES = (
    ("climate", "set_temperature"),
    ("climate", "set_hvac_mode"),
    ("switch", "turn_on"),
    ("switch", "turn_off"),
    ("select", "select_option"),
)


def record_writes(hass: HomeAssistant) -> list:
    """Record every write the controller sends, instead of reaching a device."""
    recorded: list = []

    async def record(call) -> None:
        recorded.append(call)

    for domain, service in WRITE_SERVICES:
        hass.services.async_register(domain, service, record)
    return recorded


@pytest.fixture
def calls(hass: HomeAssistant) -> list:
    """Writes recorded from before setup.

    Only the climate services survive: forwarding the platforms loads the real
    select and switch domains, which replace anything registered earlier. Use
    `start` unless the point is what happens during setup itself.
    """
    return record_writes(hass)


@pytest.fixture
def unit(hass: HomeAssistant):
    """Put the faked unit into a state the controller is content with."""

    def _set(**overrides: Any) -> None:
        scene = {
            "outdoor": "5.0",
            "fan": "2",
            "heat": "off",
            "cool": "off",
            "function": "off",
            "compressor": "off",
            "operation_mode": "manual",
            "hvac_mode": "fan_only",
            "target": 20.0,
            "current": 20.0,
            "contact": "off",
        }
        scene.update(overrides)
        hass.states.async_set(OUTDOOR, scene["outdoor"])
        hass.states.async_set(FAN, scene["fan"])
        hass.states.async_set(HEAT, scene["heat"])
        hass.states.async_set(COOL, scene["cool"])
        hass.states.async_set(FUNCTION, scene["function"])
        hass.states.async_set(COMPRESSOR, scene["compressor"])
        hass.states.async_set(OPERATION_MODE, scene["operation_mode"])
        hass.states.async_set(
            THERMOSTAT,
            scene["hvac_mode"],
            {
                "temperature": scene["target"],
                "current_temperature": scene["current"],
            },
        )
        hass.states.async_set(CONTACT, scene["contact"])

    return _set


@pytest.fixture
def entry(hass: HomeAssistant) -> MockConfigEntry:
    """A hub with one room of the unit."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Schwörer Climate Control",
        data=HUB_DATA,
        subentries_data=[
            ConfigSubentryData(
                data=ROOM_DATA,
                subentry_type=SUBENTRY_TYPE_ROOM,
                title="Wohnzimmer",
                unique_id=None,
            )
        ],
    )
    mock_entry.add_to_hass(hass)
    return mock_entry


@pytest.fixture
def setup_entry(hass: HomeAssistant):
    """Set an entry up and let it settle."""

    async def _setup(mock_entry: MockConfigEntry):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()
        return mock_entry.runtime_data

    return _setup


@pytest.fixture
def start(hass: HomeAssistant, entry: MockConfigEntry, unit):
    """Set the controller up over a faked unit, then start recording writes.

    The order is the point. Forwarding the platforms loads the real select and
    switch domains, and those replace any recorder registered before setup, so
    recording has to start afterwards.
    """

    async def _start(**scene: Any):
        unit(**scene)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return entry.runtime_data, record_writes(hass)

    return _start
