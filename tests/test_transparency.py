"""Tests for the part that answers "why": logbook, repairs, notifications."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.schwoerer_climate_control.const import (
    DOMAIN,
    EVENT_DECISION,
    ISSUE_INPUT_UNAVAILABLE,
    ISSUE_OPERATION_MODE,
    ISSUE_STUCK_WRITE,
    STUCK_AFTER,
    Mode,
)
from custom_components.schwoerer_climate_control.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import FAN, HUB_DATA, OPERATION_MODE


@pytest.fixture
def events(hass: HomeAssistant) -> list[Event]:
    """Every decision change the controller writes down."""
    recorded: list[Event] = []
    hass.bus.async_listen(EVENT_DECISION, recorded.append)
    return recorded


async def test_the_first_evaluation_says_nothing(
    hass: HomeAssistant, entry, unit, events, setup_entry
) -> None:
    unit()
    await setup_entry(entry)
    assert events == [], "there is nothing to compare the first pass against"


async def test_a_changed_decision_is_written_down(
    hass: HomeAssistant, start, events
) -> None:
    coordinator, _ = await start()
    await coordinator.async_set_mode(Mode.HEATING)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    messages = [event.data["message"] for event in events]
    assert any("Heating released" in message for message in messages)
    assert all(event.data["name"] for event in events)


async def test_an_unchanged_decision_says_nothing_again(
    hass: HomeAssistant, start, events
) -> None:
    coordinator, _ = await start()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    events.clear()

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert events == []


async def test_a_room_change_hangs_off_the_rooms_own_sensor(
    hass: HomeAssistant, start, events
) -> None:
    # Heating turns the room from idle into one with a setpoint it means, and
    # with its auxiliary heater running.
    coordinator, _ = await start()
    await coordinator.async_set_mode(Mode.HEATING)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    rooms = [event for event in events if event.data["key"] == "wohnzimmer"]
    assert rooms, "the room's own decision changed"
    assert rooms[-1].data["entity_id"] == "sensor.wohnzimmer_decision"


async def test_an_operating_mode_that_is_not_manual_is_a_repair(
    hass: HomeAssistant, start
) -> None:
    coordinator, _ = await start(operation_mode="winter")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_OPERATION_MODE)
    assert issue is not None
    assert issue.translation_placeholders == {"mode": "winter"}


async def test_the_repair_clears_when_the_unit_goes_back_to_manual(
    hass: HomeAssistant, start
) -> None:
    coordinator, _ = await start(operation_mode="winter")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_OPERATION_MODE)

    hass.states.async_set(OPERATION_MODE, "manual")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_OPERATION_MODE) is None


async def test_a_dead_sensor_is_a_repair_only_after_a_while(
    hass: HomeAssistant, start, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A sensor that misses a poll is not a repair. One with a flat battery is.
    coordinator, _ = await start(contact="unavailable")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_INPUT_UNAVAILABLE) is None

    monkeypatch.setattr(
        "custom_components.schwoerer_climate_control.coordinator.DEGRADED_GRACE",
        timedelta(0),
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_INPUT_UNAVAILABLE)
    assert issue is not None
    assert "wohnzimmer.contact[0]" in issue.translation_placeholders["inputs"]


async def test_a_write_that_never_takes_is_a_repair(
    hass: HomeAssistant, start, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "custom_components.schwoerer_climate_control.coordinator.MIN_WRITE_INTERVAL",
        timedelta(0),
    )
    coordinator, _ = await start(fan="4")
    for _ in range(STUCK_AFTER + 1):
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_STUCK_WRITE)
    assert issue is not None
    assert "fan_level" in issue.translation_placeholders["writes"]


async def test_a_release_change_is_notified_once_the_window_closes(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    hass.config_entries.async_update_entry(
        entry, data={**HUB_DATA, "notify_service": "notify.phone"}
    )
    sent: list = []

    async def record(call) -> None:
        sent.append(call)

    hass.services.async_register("notify", "phone", record)

    unit()
    coordinator = await setup_entry(entry)
    await coordinator.async_set_mode(Mode.HEATING)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert sent == [], "gathered, not sent yet"

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()

    assert len(sent) == 1
    assert "Heating released" in sent[0].data["message"]


async def test_a_fan_level_change_is_not_worth_a_message(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    hass.config_entries.async_update_entry(
        entry, data={**HUB_DATA, "notify_service": "notify.phone"}
    )
    sent: list = []

    async def record(call) -> None:
        sent.append(call)

    hass.services.async_register("notify", "phone", record)

    unit()
    coordinator = await setup_entry(entry)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    hass.states.async_set(FAN, "4")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()
    assert sent == []


async def test_diagnostics_say_what_it_would_write_and_whether_it_is_needed(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    unit(fan="4")
    await setup_entry(entry)

    report = await async_get_config_entry_diagnostics(hass, entry)
    assert report["decision"]["message"]
    assert report["controls"]["mode"] == "ventilation"
    assert report["unit"]["operation_mode"] == "manual"

    writes = {write["label"]: write for write in report["writes"]}
    assert writes["fan_level"]["needed"] is True
    assert writes["wohnzimmer.target"]["needed"] is False
    assert report["history"]
