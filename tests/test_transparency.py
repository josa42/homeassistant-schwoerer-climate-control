"""Tests for the part that answers "why": logbook, repairs, notifications."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.schwoerer_climate_control.const import (
    CONF_DECLINED_ENTITIES,
    CONF_SUPPLY_AIR_SENSOR,
    DOMAIN,
    EVENT_DECISION,
    ISSUE_INPUT_UNAVAILABLE,
    ISSUE_OPERATION_MODE,
    ISSUE_STUCK_WRITE,
    ISSUE_UNSAVED_SUGGESTION,
    STUCK_AFTER,
    Mode,
)
from custom_components.schwoerer_climate_control.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import FAN, HEAT, HUB_DATA, OPERATION_MODE, THERMOSTAT


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
    # Heating turns the room from idle into one with a setpoint it means.
    coordinator, _ = await start()
    await coordinator.async_set_mode(Mode.HEATING)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    rooms = [event for event in events if event.data["key"] == "wohnzimmer"]
    assert rooms, "the room's own decision changed"
    assert rooms[-1].data["entity_id"] == "sensor.wohnzimmer_decision"


async def test_a_write_is_sent_under_the_entry_of_the_decision_behind_it(
    hass: HomeAssistant, start, events
) -> None:
    # The shared context is what makes the logbook name the controller, and its
    # reason, as what triggered the change.
    coordinator, calls = await start(target=14.0)
    await coordinator.async_set_mode(Mode.HEATING)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    contexts = {event.data["key"]: event.context.id for event in events}
    written = {call.data["entity_id"]: call.context.id for call in calls}
    assert written[HEAT] == contexts["system"]
    assert written[THERMOSTAT] == contexts["wohnzimmer"]
    assert not any(e.data["message"].startswith("Restored: ") for e in events)


async def test_the_first_write_after_a_restart_names_the_controller(
    hass: HomeAssistant, start, events
) -> None:
    # The decision has not changed since startup, so it has no entry yet. It
    # gets one when it is carried out, and the write is sent under it.
    coordinator, calls = await start(fan="4")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert [event.data["key"] for event in events] == ["system"]
    assert events[0].data["message"].startswith("Restored: ")
    assert calls[0].data["entity_id"] == FAN
    assert calls[0].context.id == events[0].context.id


async def test_a_room_changed_by_hand_is_put_back_under_a_restored_entry(
    hass: HomeAssistant, start, unit, events
) -> None:
    coordinator, calls = await start()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert events == []

    unit(target=14.0)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert [event.data["key"] for event in events] == ["wohnzimmer"]
    assert events[0].data["message"].startswith("Restored: ")
    assert events[0].data["entity_id"] == "sensor.wohnzimmer_decision"
    assert [call.data["entity_id"] for call in calls] == [THERMOSTAT]
    assert calls[0].context.id == events[0].context.id


async def test_one_restored_entry_covers_every_write_of_its_decision(
    hass: HomeAssistant, start, events
) -> None:
    coordinator, calls = await start(fan="4", heat="on")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(events) == 1
    assert {call.data["entity_id"] for call in calls} == {FAN, HEAT}
    assert {call.context.id for call in calls} == {events[0].context.id}


async def test_a_dry_run_restores_nothing(
    hass: HomeAssistant, start, events
) -> None:
    coordinator, calls = await start(fan="4")
    await coordinator.async_set_dry_run(True)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert events == []
    assert calls == []


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


SUPPLY_AIR = "sensor.wgt_t4"


def discoverable_supply_air(hass: HomeAssistant) -> None:
    """A supply air sensor the entities form would suggest."""
    hass.states.async_set(
        SUPPLY_AIR, "45.0", {"entity_type": "temperature_t4_after_reheater"}
    )


async def test_a_suggestion_the_form_never_saved_is_a_repair(
    hass: HomeAssistant, start
) -> None:
    # The form shows it filled in, so nothing else would say it is missing.
    discoverable_supply_air(hass)
    coordinator, _ = await start()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_UNSAVED_SUGGESTION)
    assert issue is not None
    assert issue.translation_placeholders == {"entities": SUPPLY_AIR}


async def test_the_repair_clears_once_the_suggestion_is_saved(
    hass: HomeAssistant, entry, start
) -> None:
    discoverable_supply_air(hass)
    coordinator, _ = await start()
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_UNSAVED_SUGGESTION)

    hass.config_entries.async_update_entry(
        entry, options={CONF_SUPPLY_AIR_SENSOR: SUPPLY_AIR}
    )
    await hass.async_block_till_done()
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_UNSAVED_SUGGESTION) is None


async def test_a_declined_suggestion_is_not_a_repair(
    hass: HomeAssistant, entry, start
) -> None:
    hass.config_entries.async_update_entry(
        entry, options={CONF_DECLINED_ENTITIES: [CONF_SUPPLY_AIR_SENSOR]}
    )
    discoverable_supply_air(hass)
    coordinator, _ = await start()
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_UNSAVED_SUGGESTION) is None


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


async def test_a_notify_entity_is_sent_to_through_send_message(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    hass.config_entries.async_update_entry(
        entry, data={**HUB_DATA, "notify_service": "notify.phone"}
    )
    sent: list = []

    async def record(call) -> None:
        sent.append(call)

    hass.services.async_register("notify", "send_message", record)

    unit()
    coordinator = await setup_entry(entry)
    await coordinator.async_set_mode(Mode.HEATING)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()

    assert len(sent) == 1
    assert sent[0].data["entity_id"] == "notify.phone"
    assert "Heating released" in sent[0].data["message"]


async def test_a_notification_that_cannot_be_sent_is_logged(
    hass: HomeAssistant, entry, unit, setup_entry, caplog
) -> None:
    hass.config_entries.async_update_entry(
        entry, data={**HUB_DATA, "notify_service": "notify.phone"}
    )

    unit()
    coordinator = await setup_entry(entry)
    await coordinator.async_set_mode(Mode.HEATING)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()

    assert "Could not send notification to notify.phone" in caplog.text


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


async def test_a_restored_entry_is_not_worth_a_message(
    hass: HomeAssistant, entry, unit, setup_entry, events
) -> None:
    hass.config_entries.async_update_entry(
        entry,
        data={
            **HUB_DATA,
            "notify_service": "notify.phone",
            "notify_every_change": True,
        },
    )
    sent: list = []

    async def record(call) -> None:
        sent.append(call)

    hass.services.async_register("notify", "phone", record)

    unit(fan="4")
    coordinator = await setup_entry(entry)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert events, "the write was restored"

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()
    assert sent == []


@pytest.mark.parametrize("every_change", [False, True])
async def test_a_change_without_a_release_is_notified_only_when_asked_for(
    hass: HomeAssistant, entry, unit, setup_entry, every_change: bool
) -> None:
    hass.config_entries.async_update_entry(
        entry,
        data={
            **HUB_DATA,
            "notify_service": "notify.phone",
            "notify_every_change": every_change,
        },
    )
    sent: list = []

    async def record(call) -> None:
        sent.append(call)

    hass.services.async_register("notify", "phone", record)

    unit()
    coordinator = await setup_entry(entry)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    # Holiday lowers the room's target and the fan, but releases nothing.
    await coordinator.async_set_holiday(True)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()

    if not every_change:
        assert sent == []
        return
    assert len(sent) == 1
    assert "Wohnzimmer: " in sent[0].data["message"]


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
