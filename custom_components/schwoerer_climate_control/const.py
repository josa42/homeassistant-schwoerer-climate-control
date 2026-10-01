"""Constants for the Schwörer Climate Control integration."""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum

DOMAIN = "schwoerer_climate_control"

#: The integration whose entities this one reads and drives.
SCHWOERER_LUEFTUNG_DOMAIN = "schwoerer_lueftung"

################################################################################
# Timings
#
# These are not configurable. Each one protects the device or the database, and
# a user who can lower them can only do harm.

#: The release of the heat pump is not changed again until it has been stable
#: this long, unless the compressor is standing still anyway. Taken from the
#: hand-written automation this integration replaces, where it has held up.
#: Without it the release flips as often as the outdoor reading crosses the
#: threshold, which is short-cycling the compressor.
RELEASE_LOCKOUT = timedelta(minutes=30)

#: A contact has to hold its state this long before it counts. Covers a reed
#: switch that chatters as a window is pulled shut.
CONTACT_DWELL = timedelta(minutes=1)

#: How long CO₂ has to stay above the threshold before the fan reacts. A single
#: breath into the sensor is not a reason to run the fan harder.
CO2_DWELL = timedelta(minutes=5)

#: How old the outdoor reading may be before it stops being usable. Beyond this
#: the mode falls back to ventilation, which is the one state that is never
#: wrong without data.
OUTDOOR_MAX_AGE = timedelta(minutes=30)

#: How long PV surplus has to hold before it is allowed to raise a setpoint.
#: Long enough that a cloud gap is not an invitation to heat the house.
PV_SURPLUS_DWELL = timedelta(minutes=20)


class Mode(StrEnum):
    """Which direction of energy is allowed.

    Named after the direction rather than the season, so that a rule can read
    the gate it cares about instead of asking what month it is. Ventilation is
    the fallback: neither heating nor cooling, base function still running.
    """

    HEATING = "heating"
    VENTILATION = "ventilation"
    COOLING = "cooling"


class FanMode(StrEnum):
    """How the fan level is chosen, when it is not a fixed stage."""

    AUTOMATIC = "automatic"
    QUIET = "quiet"
    BOOST = "boost"


class HeatingCoolingFunction(StrEnum):
    """Register 230, which gates the bypass as a side effect.

    The damper closes within seconds of this leaving ``cooling``, so cooling
    cannot be left to the heat pump release alone.
    """

    OFF = "off"
    HEATING = "heating"
    COOLING = "cooling"


class Intent(StrEnum):
    """What the system decided to do, as one word."""

    DISABLED = "disabled"
    HEATING = "heating"
    COOLING = "cooling"
    VENTILATION = "ventilation"


class RoomIntent(StrEnum):
    """What a room's setpoint is for."""

    DISABLED = "disabled"
    WINDOW_OPEN = "window_open"
    HOLIDAY = "holiday"
    NIGHT = "night"
    NORMAL = "normal"
    COOLING = "cooling"
    #: Neither heating nor cooling is allowed. The setpoint is still written so
    #: the device shows a sensible number and means it again the moment the
    #: mode returns to heating.
    IDLE = "idle"


class Reason(StrEnum):
    """Stable reason codes.

    The sentence a person reads is built from these plus the decision's
    numbers, so an automation matches on the code and never on prose.
    """

    CONTROLLER_DISABLED = "controller_disabled"
    OUTDOOR_UNAVAILABLE = "outdoor_unavailable"
    HEAT_RELEASED = "heat_released"
    HEAT_TOO_WARM = "heat_too_warm"
    COOL_RELEASED = "cool_released"
    COOL_NOT_NEEDED = "cool_not_needed"
    RELEASE_LOCKED = "release_locked"
    VENTILATION_ONLY = "ventilation_only"
    FORECAST_WARM = "forecast_warm"


class FanReason(StrEnum):
    """Why the fan level is what it is."""

    FIXED_STAGE = "fixed_stage"
    BOOST = "boost"
    CO2_HIGH = "co2_high"
    HUMIDITY_HIGH = "humidity_high"
    NIGHT_COOLING = "night_cooling"
    HOLIDAY = "holiday"
    NIGHT = "night"
    NORMAL = "normal"


class RoomReason(StrEnum):
    """Why a room's setpoint is what it is."""

    CONTROLLER_DISABLED = "controller_disabled"
    WINDOW_OPEN = "window_open"
    CONTACT_UNAVAILABLE = "contact_unavailable"
    HOLIDAY = "holiday"
    NIGHT_SETBACK = "night_setback"
    NORMAL = "normal"
    COOLING = "cooling"
    VENTILATION_ONLY = "ventilation_only"
    PV_SURPLUS = "pv_surplus"


################################################################################
# Configuration keys

CONF_ROOMS = "rooms"
CONF_NAME = "name"

# Heating setpoints.
CONF_TARGET_NORMAL = "target_normal"
CONF_TARGET_NIGHT = "target_night"
CONF_TARGET_HOLIDAY = "target_holiday"
CONF_TARGET_WINDOW_OPEN = "target_window_open"

# Cooling setpoints. A target below the room temperature is both the intent and
# the condition the unit opens the bypass on, so one number does both jobs.
CONF_TARGET_COOL = "target_cool"
CONF_TARGET_COOL_HOLIDAY = "target_cool_holiday"
CONF_TARGET_COOL_WINDOW_OPEN = "target_cool_window_open"

# Night window.
CONF_NIGHT_START = "night_start"
CONF_NIGHT_END = "night_end"

# Releases.
CONF_HEAT_RELEASE_BELOW = "heat_release_below"
CONF_RELEASE_HYSTERESIS = "release_hysteresis"
CONF_FORECAST_BLOCKS_ABOVE = "forecast_blocks_above"
CONF_AUX_HEAT_BELOW = "aux_heat_below"
CONF_AUX_HEAT_OFF_AT_NIGHT = "aux_heat_off_at_night"
CONF_COOL_RELEASE_ABOVE = "cool_release_above"

# Fan.
CONF_FAN_NORMAL = "fan_normal"
CONF_FAN_NIGHT = "fan_night"
CONF_FAN_HOLIDAY = "fan_holiday"
CONF_FAN_QUIET_MAX = "fan_quiet_max"
CONF_FAN_BOOST = "fan_boost"
CONF_FAN_AIR_QUALITY = "fan_air_quality"
CONF_FAN_NIGHT_COOLING = "fan_night_cooling"

# Air quality thresholds.
CONF_HUMIDITY_HIGH = "humidity_high"
CONF_CO2_HIGH = "co2_high"

# PV surplus.
CONF_PV_SURPLUS_ABOVE = "pv_surplus_above"
CONF_PV_TARGET_BOOST = "pv_target_boost"

#: The lowest and highest the device accepts for a room setpoint. Asking for
#: anything outside this is rejected by the field rather than clamped, so the
#: engine clamps.
TARGET_MIN = 10.0
TARGET_MAX = 30.0

FAN_MIN = 0
FAN_MAX = 4

DEFAULTS: dict[str, object] = {
    CONF_TARGET_NORMAL: 20.0,
    CONF_TARGET_NIGHT: 19.0,
    CONF_TARGET_HOLIDAY: 18.0,
    CONF_TARGET_WINDOW_OPEN: 12.0,
    CONF_TARGET_COOL: 24.0,
    CONF_TARGET_COOL_HOLIDAY: 26.0,
    CONF_TARGET_COOL_WINDOW_OPEN: 28.0,
    CONF_NIGHT_START: "20:00",
    CONF_NIGHT_END: "05:00",
    CONF_HEAT_RELEASE_BELOW: 16.0,
    CONF_RELEASE_HYSTERESIS: 1.0,
    CONF_FORECAST_BLOCKS_ABOVE: 5.0,
    CONF_AUX_HEAT_BELOW: 10.0,
    CONF_AUX_HEAT_OFF_AT_NIGHT: False,
    CONF_COOL_RELEASE_ABOVE: 26.0,
    CONF_FAN_NORMAL: 2,
    CONF_FAN_NIGHT: 1,
    CONF_FAN_HOLIDAY: 1,
    CONF_FAN_QUIET_MAX: 1,
    CONF_FAN_BOOST: 3,
    CONF_FAN_AIR_QUALITY: 3,
    CONF_FAN_NIGHT_COOLING: 3,
    CONF_HUMIDITY_HIGH: 70.0,
    CONF_CO2_HIGH: 1000.0,
    CONF_PV_SURPLUS_ABOVE: 1500.0,
    CONF_PV_TARGET_BOOST: 1.0,
}

#: Settings a room may override. Everything else is the hub's alone, because a
#: release or a fan level is one device-wide decision whatever a room wants.
OVERRIDABLE: tuple[str, ...] = (
    CONF_TARGET_NORMAL,
    CONF_TARGET_NIGHT,
    CONF_TARGET_HOLIDAY,
    CONF_TARGET_WINDOW_OPEN,
    CONF_TARGET_COOL,
    CONF_TARGET_COOL_HOLIDAY,
    CONF_TARGET_COOL_WINDOW_OPEN,
    CONF_NIGHT_START,
    CONF_NIGHT_END,
    CONF_AUX_HEAT_BELOW,
    CONF_AUX_HEAT_OFF_AT_NIGHT,
    CONF_HUMIDITY_HIGH,
    CONF_CO2_HIGH,
)
