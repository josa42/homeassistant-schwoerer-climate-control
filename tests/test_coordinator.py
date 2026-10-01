"""Tests for the thing that writes: it must write as little as it possibly can."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant

from custom_components.schwoerer_climate_control.const import STUCK_AFTER, Mode

from .conftest import FAN, HEAT, OPERATION_MODE, THERMOSTAT


async def test_the_first_evaluation_never_writes(
    hass: HomeAssistant, entry, unit, calls, setup_entry
) -> None:
    # The controls restore after setup, so acting on this pass would act on
    # defaults, and a restart would write the ventilation mode over the real one.
    # The thermostat is the one writer whose recorder survives platform setup,
    # so its setpoint is set wrong on purpose: a write here would show up.
    unit(target=14.0)
    await setup_entry(entry)
    assert calls == []


async def test_a_settled_house_is_not_written_to(hass: HomeAssistant, start) -> None:
    coordinator, calls = await start()

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert calls == [], "a steady state must leave the bus alone"


async def test_only_what_differs_is_written(hass: HomeAssistant, start) -> None:
    coordinator, calls = await start(fan="4")

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert [call.data["entity_id"] for call in calls] == [FAN]
    assert calls[0].data["option"] == "2"


async def test_a_value_the_device_is_not_reporting_is_not_a_difference(
    hass: HomeAssistant, start
) -> None:
    coordinator, calls = await start()
    hass.states.async_set(FAN, "unavailable")

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert calls == [], "not knowing is not a reason to write"


async def test_a_setpoint_within_the_devices_resolution_is_left_alone(
    hass: HomeAssistant, start
) -> None:
    # The device stores tenths, so 20.02 and 20.0 are the same setpoint.
    coordinator, calls = await start(target=20.02)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert calls == []


async def test_a_setpoint_that_really_differs_is_written(
    hass: HomeAssistant, start
) -> None:
    coordinator, calls = await start(target=14.0)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    written = {call.data["entity_id"]: call for call in calls}
    assert written[THERMOSTAT].data["temperature"] == 20.0


async def test_dry_run_decides_everything_and_writes_nothing(
    hass: HomeAssistant, start
) -> None:
    coordinator, calls = await start(fan="4")
    await coordinator.async_set_dry_run(True)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert calls == []
    assert coordinator.data.fan_level == 2, "it still decided, it just said nothing"


async def test_a_second_bundle_waits_for_the_rate_limit(
    hass: HomeAssistant, start
) -> None:
    coordinator, calls = await start(fan="4")

    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(calls) == 1

    # The fan never took the value, so the same write is still wanted.
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(calls) == 1, "held back by the minimum interval"


async def test_a_write_that_never_takes_is_reported(
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

    assert "fan_level" in coordinator.stuck_writes


async def test_a_write_that_takes_clears_the_counter(
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
    assert coordinator.stuck_writes

    hass.states.async_set(FAN, "2")
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.stuck_writes == ()


async def test_heating_mode_releases_the_heat_pump(hass: HomeAssistant, start) -> None:
    coordinator, calls = await start(outdoor="5.0")
    await coordinator.async_set_mode(Mode.HEATING)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    heat = [call for call in calls if call.data["entity_id"] == HEAT]
    assert [call.service for call in heat] == ["turn_on"]


async def test_a_disabled_controller_writes_nothing_at_all(
    hass: HomeAssistant, start
) -> None:
    coordinator, calls = await start(fan="4", heat="on")
    await coordinator.async_set_enabled(False)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert calls == []
    assert coordinator.data.intent.value == "disabled"


async def test_the_entities_appear(hass: HomeAssistant, entry, unit, setup_entry) -> None:
    unit()
    await setup_entry(entry)

    for entity_id in (
        "switch.schworer_climate_control_active",
        "switch.schworer_climate_control_holiday",
        "switch.schworer_climate_control_dry_run",
        "select.schworer_climate_control_mode",
        "select.schworer_climate_control_fan",
        "sensor.schworer_climate_control_decision",
        "binary_sensor.schworer_climate_control_degraded",
        "sensor.wohnzimmer_decision",
    ):
        assert hass.states.get(entity_id) is not None, entity_id


async def test_the_decision_sensor_carries_the_reasoning(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    unit()
    await setup_entry(entry)
    state = hass.states.get("sensor.schworer_climate_control_decision")
    assert state is not None
    assert state.attributes["message"]
    assert state.attributes["gates"]
    assert state.attributes["inputs"]["outdoor"]["value"] == 5.0
    assert state.attributes["settings"]["heat_release_below"]["source"] == "default"


async def test_the_room_sensor_says_what_its_setpoint_is_for(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    unit()
    await setup_entry(entry)
    state = hass.states.get("sensor.wohnzimmer_decision")
    assert state is not None
    assert state.attributes["target_temperature"] == 20.0
    assert state.attributes["settings"]["target_normal"]["source"] == "default"


async def test_a_dead_contact_shows_up_as_degraded(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    unit(contact="unavailable")
    await setup_entry(entry)

    degraded = hass.states.get("binary_sensor.schworer_climate_control_degraded")
    assert degraded is not None
    assert degraded.state == "on"
    assert degraded.attributes["failed_inputs"] == ["wohnzimmer.contact[0]"]


@pytest.mark.parametrize("mode", ["winter", "summer", "off"])
async def test_the_operating_mode_is_read_not_written(
    hass: HomeAssistant, start, mode: str
) -> None:
    coordinator, calls = await start(operation_mode=mode)

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.operation_mode == mode
    assert OPERATION_MODE not in {call.data["entity_id"] for call in calls}


async def test_the_recovery_sensor_only_exists_when_it_can_say_something(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    unit()
    await setup_entry(entry)
    assert hass.states.get("sensor.schworer_climate_control_heat_recovery") is None


async def test_the_recovery_sensor_reports_a_damper_that_moves_no_air(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    from .conftest import HUB_DATA

    hass.config_entries.async_update_entry(
        entry,
        data={
            **HUB_DATA,
            "supply_temperature_sensor": "sensor.t3",
            "extract_temperature_sensor": "sensor.t5",
            "bypass_sensor": "sensor.bypass",
        },
    )
    unit(outdoor="7.0")
    hass.states.async_set("sensor.t3", "21.0")
    hass.states.async_set("sensor.t5", "22.0")
    hass.states.async_set("sensor.bypass", "open_cooling")
    await setup_entry(entry)

    state = hass.states.get("sensor.schworer_climate_control_heat_recovery")
    assert state is not None
    assert float(state.state) == pytest.approx(93.3, abs=0.1)
    assert state.attributes["bypass_open"] is True
    assert state.attributes["bypass_effective"] is False, "open, and recovering anyway"
