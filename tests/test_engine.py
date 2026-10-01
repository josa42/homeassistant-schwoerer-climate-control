"""Tests for the decision engine: the gates, the lockout and the priorities."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

import pytest

from custom_components.schwoerer_climate_control.const import (
    CONF_AUX_HEAT_OFF_AT_NIGHT,
    CONF_CO2_HIGH,
    CONF_FAN_AIR_QUALITY,
    CONF_FAN_QUIET_MAX,
    CONF_HUMIDITY_HIGH,
    CONF_TARGET_NORMAL,
    FanMode,
    FanReason,
    HeatingCoolingFunction,
    Intent,
    Mode,
    Reason,
    RoomIntent,
    RoomReason,
)
from custom_components.schwoerer_climate_control.engine import (
    EngineState,
    Inputs,
    RoomInputs,
    evaluate,
)
from custom_components.schwoerer_climate_control.models import Reading

NOON = datetime(2026, 1, 15, 12, 0)
NIGHT = datetime(2026, 1, 15, 22, 0)

LONG = timedelta(hours=2)
BRIEF = timedelta(minutes=5)


def read(value: Any, *, age: timedelta = BRIEF, stable: timedelta = LONG) -> Reading:
    return Reading(value=value, updated_ago=age, stable_for=stable)


def a_room(room_id: str = "wohnzimmer", **overrides: Any) -> RoomInputs:
    defaults: dict[str, Any] = {
        "room_id": room_id,
        "name": room_id.title(),
        "temperature": read(20.0),
        "contacts": (read(False),),
    }
    defaults.update(overrides)
    return RoomInputs(**defaults)


def given(**overrides: Any) -> Inputs:
    defaults: dict[str, Any] = {
        "now": NOON,
        "outdoor": read(5.0),
        "heat_release": read(False),
        "cool_release": read(False),
        "compressor_running": read(False),
        "rooms": (a_room(),),
    }
    defaults.update(overrides)
    return Inputs(**defaults)


def run(
    inputs: Inputs | None = None,
    hub: dict[str, Any] | None = None,
    state: EngineState | None = None,
    *,
    enabled: bool = True,
    mode: Mode = Mode.HEATING,
    fan_request: Any = FanMode.AUTOMATIC,
    holiday: bool = False,
):
    return evaluate(
        inputs or given(),
        hub or {},
        state or EngineState(),
        enabled=enabled,
        mode=mode,
        fan_request=fan_request,
        holiday=holiday,
    )


################################################################################
# The heating release


def test_releases_heating_when_it_is_cold() -> None:
    decision, _ = run()
    assert decision.heat_release is True
    assert decision.reason is Reason.HEAT_RELEASED
    assert decision.heating_cooling_function is HeatingCoolingFunction.HEATING
    assert "5.0" in decision.message


def test_blocks_heating_when_it_is_warm() -> None:
    decision, _ = run(given(outdoor=read(18.0)))
    assert decision.heat_release is False
    assert decision.reason is Reason.HEAT_TOO_WARM


def test_hysteresis_keeps_a_running_release_past_the_threshold() -> None:
    # 16.5 is above the 16.0 threshold but inside the 1.0 band, so a release
    # that is already on stays on.
    warm = given(outdoor=read(16.5), heat_release=read(True))
    assert run(warm)[0].heat_release is True

    # The same reading does not turn it on in the first place.
    assert run(given(outdoor=read(16.5)))[0].heat_release is False


def test_release_is_not_moved_while_the_compressor_runs_on_a_fresh_change() -> None:
    inputs = given(
        outdoor=read(5.0),
        heat_release=read(False, stable=BRIEF),
        compressor_running=read(True),
    )
    decision, _ = run(inputs)
    assert decision.heat_release is None, "a locked release must not be written"
    assert decision.reason is Reason.RELEASE_LOCKED
    assert decision.gate_passed("release_lockout") is False


def test_release_moves_while_the_compressor_is_idle() -> None:
    inputs = given(
        heat_release=read(False, stable=BRIEF),
        compressor_running=read(False),
    )
    decision, _ = run(inputs)
    assert decision.heat_release is True
    assert decision.gate_passed("release_lockout") is True


def test_release_moves_once_it_has_been_stable_long_enough() -> None:
    inputs = given(
        heat_release=read(False, stable=timedelta(minutes=31)),
        compressor_running=read(True),
    )
    assert run(inputs)[0].heat_release is True


def test_a_locked_release_keeps_the_auxiliary_heater_off() -> None:
    # The auxiliary heater follows what the heat pump is actually doing, not
    # what the controller would have liked it to do.
    inputs = given(
        heat_release=read(False, stable=BRIEF),
        compressor_running=read(True),
    )
    decision, _ = run(inputs)
    assert decision.rooms[0].auxiliary_heat is False


################################################################################
# The forecast


def test_a_warm_forecast_blocks_heating_on_a_mild_morning() -> None:
    inputs = given(outdoor=read(8.0), forecast_max=read(17.0))
    decision, _ = run(inputs)
    assert decision.heat_release is False
    assert decision.reason is Reason.FORECAST_WARM


def test_a_warm_forecast_does_not_block_heating_on_a_cold_morning() -> None:
    # Below the floor the forecast gets no say: a day that starts at -2 needs
    # the compressor whatever the afternoon brings.
    inputs = given(outdoor=read(-2.0), forecast_max=read(17.0))
    decision, _ = run(inputs)
    assert decision.heat_release is True


################################################################################
# Missing inputs


def test_a_stale_outdoor_reading_falls_back_to_ventilation() -> None:
    inputs = given(outdoor=read(5.0, age=timedelta(hours=3)))
    decision, _ = run(inputs)
    assert decision.mode is Mode.VENTILATION
    assert decision.requested_mode is Mode.HEATING
    assert decision.reason is Reason.OUTDOOR_UNAVAILABLE
    assert decision.heat_release is False
    assert decision.heating_cooling_function is HeatingCoolingFunction.OFF
    assert "outdoor" in decision.degraded


def test_an_unreadable_contact_counts_as_an_open_window() -> None:
    inputs = given(rooms=(a_room(contacts=(Reading(),)),))
    decision, _ = run(inputs)
    room = decision.rooms[0]
    assert room.window_open is True
    assert room.reason is RoomReason.WINDOW_OPEN
    assert room.target_temperature == 12.0
    assert "wohnzimmer.contact[0]" in decision.degraded


def test_a_missing_room_temperature_keeps_the_setpoint_and_drops_the_heater() -> None:
    inputs = given(rooms=(a_room(temperature=Reading()),))
    decision, _ = run(inputs)
    room = decision.rooms[0]
    assert room.target_temperature == 20.0
    assert room.auxiliary_heat is False
    assert "wohnzimmer.temperature" in decision.degraded


################################################################################
# Room setpoints


def test_night_setback() -> None:
    decision, _ = run(given(now=NIGHT))
    assert decision.rooms[0].target_temperature == 19.0
    assert decision.rooms[0].reason is RoomReason.NIGHT_SETBACK
    assert decision.is_night is True


def test_holiday_beats_the_night_setback() -> None:
    decision, _ = run(given(now=NIGHT), holiday=True)
    assert decision.rooms[0].target_temperature == 18.0
    assert decision.rooms[0].reason is RoomReason.HOLIDAY


def test_an_open_window_beats_everything() -> None:
    inputs = given(now=NIGHT, rooms=(a_room(contacts=(read(True),)),))
    decision, _ = run(inputs, holiday=True)
    assert decision.rooms[0].target_temperature == 12.0
    assert decision.rooms[0].intent is RoomIntent.WINDOW_OPEN


def test_a_window_that_just_opened_does_not_count_yet() -> None:
    inputs = given(rooms=(a_room(contacts=(read(True, stable=timedelta(seconds=20)),)),))
    assert run(inputs)[0].rooms[0].window_open is False


def test_a_room_setting_overrides_the_hub_and_says_so() -> None:
    inputs = given(rooms=(a_room(config={CONF_TARGET_NORMAL: 18.5}),))
    decision, _ = run(inputs, {CONF_TARGET_NORMAL: 21.0})
    room = decision.rooms[0]
    assert room.target_temperature == 18.5
    assert room.settings[CONF_TARGET_NORMAL] == {"value": 18.5, "source": "room"}


def test_a_setpoint_is_clamped_to_what_the_device_accepts() -> None:
    decision, _ = run(given(), {CONF_TARGET_NORMAL: 45.0})
    assert decision.rooms[0].target_temperature == 30.0


################################################################################
# The auxiliary heater


def test_the_auxiliary_heater_runs_when_it_is_cold_and_heating_is_released() -> None:
    assert run(given(outdoor=read(5.0)))[0].rooms[0].auxiliary_heat is True


def test_the_auxiliary_heater_stays_off_when_it_is_not_cold_enough() -> None:
    # Heating is released below 16, the second stage only below 10.
    decision, _ = run(given(outdoor=read(12.0)))
    assert decision.heat_release is True
    assert decision.rooms[0].auxiliary_heat is False
    assert decision.rooms[0].gate_passed("aux_outdoor_cold") is False


def test_the_auxiliary_heater_is_off_at_night_in_a_bedroom() -> None:
    bedroom = a_room("schlafzimmer", config={CONF_AUX_HEAT_OFF_AT_NIGHT: True})
    decision, _ = run(given(now=NIGHT, rooms=(bedroom, a_room())))
    by_name = {room.room_id: room for room in decision.rooms}
    assert by_name["schlafzimmer"].auxiliary_heat is False
    assert by_name["wohnzimmer"].auxiliary_heat is True


def test_a_room_without_an_auxiliary_heater_is_never_written() -> None:
    inputs = given(rooms=(a_room(has_auxiliary_heat=False),))
    assert run(inputs)[0].rooms[0].auxiliary_heat is None


def test_an_open_window_keeps_the_auxiliary_heater_off() -> None:
    inputs = given(rooms=(a_room(contacts=(read(True),)),))
    assert run(inputs)[0].rooms[0].auxiliary_heat is False


################################################################################
# The fan


def test_the_fan_follows_the_time_of_day() -> None:
    assert run()[0].fan_level == 2
    assert run(given(now=NIGHT))[0].fan_level == 1
    assert run(holiday=True)[0].fan_level == 1


def test_humidity_beats_the_night_setting() -> None:
    bath = a_room("bad", humidity=read(76.0))
    decision, _ = run(given(now=NIGHT, rooms=(bath,)))
    assert decision.fan_level == 3
    assert decision.fan_reason is FanReason.HUMIDITY_HIGH
    assert decision.fan_requested_by == "Bad"


def test_the_humidity_threshold_is_overridable_per_room() -> None:
    bath = a_room("bad", humidity=read(62.0), config={CONF_HUMIDITY_HIGH: 60.0})
    decision, _ = run(given(rooms=(bath,)))
    assert decision.fan_level == 3
    assert decision.fan_reason is FanReason.HUMIDITY_HIGH


def test_a_room_with_an_open_window_asks_for_nothing() -> None:
    # Its humidity sensor is measuring outdoors.
    bath = a_room("bad", humidity=read(90.0), contacts=(read(True),))
    assert run(given(rooms=(bath,)))[0].fan_level == 2


def test_co2_only_counts_once_it_has_been_high_for_long_enough() -> None:
    room = a_room("kinderzimmer", co2=read(1400.0))
    inputs = given(rooms=(room,))

    first, state = run(inputs)
    assert first.fan_level == 2, "the dwell timer has only just started"
    assert state.co2_high_since["kinderzimmer"] == NOON

    later = replace(inputs, now=NOON + timedelta(minutes=6))
    decision, _ = run(later, state=state)
    assert decision.fan_level == 3
    assert decision.fan_reason is FanReason.CO2_HIGH


def test_co2_falling_back_below_the_threshold_clears_the_timer() -> None:
    room = a_room("kinderzimmer", co2=read(1400.0))
    _, state = run(given(rooms=(room,)))
    cleared = given(rooms=(a_room("kinderzimmer", co2=read(600.0)),))
    _, state = run(cleared, state=state)
    assert state.co2_high_since == {}


def test_co2_threshold_is_overridable_per_room() -> None:
    room = a_room("kinderzimmer", co2=read(900.0), config={CONF_CO2_HIGH: 800.0})
    _, state = run(given(rooms=(room,)))
    assert "kinderzimmer" in state.co2_high_since


def test_quiet_caps_the_level_and_records_what_it_capped() -> None:
    bath = a_room("bad", humidity=read(76.0))
    decision, _ = run(given(rooms=(bath,)), fan_request=FanMode.QUIET)
    assert decision.fan_level == 1
    assert decision.fan_capped_from == 3
    assert decision.fan_reason is FanReason.HUMIDITY_HIGH, "the cap is not the reason"
    assert "capped from 3" in decision.message


def test_quiet_leaves_a_level_below_the_ceiling_alone() -> None:
    decision, _ = run(hub={CONF_FAN_QUIET_MAX: 2}, fan_request=FanMode.QUIET)
    assert decision.fan_level == 2
    assert decision.fan_capped_from is None


def test_boost_raises_the_level() -> None:
    decision, _ = run(fan_request=FanMode.BOOST)
    assert decision.fan_level == 3
    assert decision.fan_reason is FanReason.BOOST


def test_boost_does_not_lower_a_higher_demand() -> None:
    hot = a_room("bad", humidity=read(99.0))
    decision, _ = run(
        given(rooms=(hot,)), {CONF_FAN_AIR_QUALITY: 4}, fan_request=FanMode.BOOST
    )
    assert decision.fan_level == 4


def test_a_fixed_stage_wins_including_zero() -> None:
    bath = a_room("bad", humidity=read(90.0))
    decision, _ = run(given(rooms=(bath,)), fan_request=0)
    assert decision.fan_level == 0
    assert decision.fan_reason is FanReason.FIXED_STAGE


################################################################################
# Cooling


def test_cooling_uses_the_cooling_setpoint_and_keeps_the_damper_gate_open() -> None:
    inputs = given(outdoor=read(28.0), rooms=(a_room(temperature=read(27.0)),))
    decision, _ = run(inputs, mode=Mode.COOLING)
    assert decision.rooms[0].target_temperature == 24.0
    assert decision.rooms[0].intent is RoomIntent.COOLING
    assert decision.heating_cooling_function is HeatingCoolingFunction.COOLING
    assert decision.heat_release is False


def test_cooling_is_released_when_a_room_is_too_warm() -> None:
    inputs = given(outdoor=read(30.0), rooms=(a_room(temperature=read(27.0)),))
    decision, _ = run(inputs, mode=Mode.COOLING)
    assert decision.cool_release is True
    assert decision.reason is Reason.COOL_RELEASED


def test_cooling_is_not_released_for_a_house_that_is_warm_enough() -> None:
    inputs = given(outdoor=read(30.0), rooms=(a_room(temperature=read(24.0)),))
    decision, _ = run(inputs, mode=Mode.COOLING)
    assert decision.cool_release is False
    assert decision.reason is Reason.COOL_NOT_NEEDED


def test_night_cooling_raises_the_fan_when_it_is_cooler_outside() -> None:
    inputs = given(now=NIGHT, outdoor=read(16.0), rooms=(a_room(temperature=read(26.0)),))
    decision, _ = run(inputs, mode=Mode.COOLING)
    assert decision.fan_level == 3
    assert decision.fan_reason is FanReason.NIGHT_COOLING


def test_cooling_never_asks_for_stage_zero() -> None:
    # Stage 0 shuts the damper, which is the opposite of what cooling wants.
    inputs = given(outdoor=read(28.0), rooms=(a_room(temperature=read(27.0)),))
    decision, _ = run(
        inputs, {CONF_FAN_QUIET_MAX: 0}, mode=Mode.COOLING, fan_request=FanMode.QUIET
    )
    assert decision.fan_level == 1


################################################################################
# Ventilation and off


def test_ventilation_allows_neither_direction_but_keeps_the_setpoint() -> None:
    decision, _ = run(mode=Mode.VENTILATION)
    assert decision.heat_release is False
    assert decision.cool_release is False
    assert decision.heating_cooling_function is HeatingCoolingFunction.OFF
    assert decision.intent is Intent.VENTILATION
    assert decision.reason is Reason.VENTILATION_ONLY
    room = decision.rooms[0]
    assert room.intent is RoomIntent.IDLE
    assert room.target_temperature == 20.0
    assert room.auxiliary_heat is False


def test_a_disabled_controller_writes_nothing() -> None:
    decision, _ = run(enabled=False)
    assert decision.intent is Intent.DISABLED
    assert decision.heat_release is None
    assert decision.cool_release is None
    assert decision.heating_cooling_function is None
    assert decision.fan_level is None
    assert decision.rooms[0].target_temperature is None
    assert decision.rooms[0].auxiliary_heat is None


def test_a_disabled_controller_still_carries_the_dwell_timers() -> None:
    room = a_room("kinderzimmer", co2=read(1400.0))
    _, state = run(given(rooms=(room,)), enabled=False)
    assert state.co2_high_since["kinderzimmer"] == NOON


################################################################################
# PV surplus


def test_pv_surplus_raises_the_setpoint_only_once_it_has_held() -> None:
    inputs = given(pv_power=read(3000.0))
    first, state = run(inputs)
    assert first.rooms[0].target_temperature == 20.0

    later = replace(inputs, now=NOON + timedelta(minutes=25))
    decision, _ = run(later, state=state)
    assert decision.rooms[0].target_temperature == 21.0
    assert decision.rooms[0].reason is RoomReason.PV_SURPLUS


def test_pv_surplus_is_not_stored_in_a_room_with_an_open_window() -> None:
    inputs = given(pv_power=read(3000.0), rooms=(a_room(contacts=(read(True),)),))
    _, state = run(inputs)
    later = replace(inputs, now=NOON + timedelta(minutes=25))
    assert run(later, state=state)[0].rooms[0].target_temperature == 12.0


def test_pv_surplus_dropping_out_restarts_the_clock() -> None:
    _, state = run(given(pv_power=read(3000.0)))
    _, state = run(given(pv_power=read(100.0)), state=state)
    assert state.pv_surplus_since is None


################################################################################
# The record


@pytest.mark.parametrize("mode", list(Mode))
def test_every_decision_carries_its_inputs_and_settings(mode: Mode) -> None:
    decision, _ = run(given(forecast_max=read(12.0), pv_power=read(500.0)), mode=mode)
    assert decision.inputs["outdoor"]["value"] == 5.0
    assert decision.inputs["outdoor"]["age"] == BRIEF.total_seconds()
    assert decision.settings["heat_release_below"]["source"] == "default"
    assert decision.as_dict()["rooms"][0]["name"] == "Wohnzimmer"
    assert decision.as_attributes()["mode"] == str(mode)
