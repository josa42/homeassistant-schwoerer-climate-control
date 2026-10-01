"""Setting the controller up: the unit once, then a room at a time.

The unit's entities are discovered and offered as suggestions, so the first form
is normally a matter of confirming it. Rooms are subentries, which gives each one
its own device and its own dialog, and lets a room the unit does not heat sit
next to the six that it does.

Every per-room setting is optional. Left empty it inherits the hub's value, and
that is what lets a decision say which level a number came from.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryData,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ACTUATOR,
    CONF_ADD_ROOMS,
    CONF_AUX_HEAT_BELOW,
    CONF_AUX_HEAT_OFF_AT_NIGHT,
    CONF_BYPASS_SENSOR,
    CONF_CLIMATE_ENTITY,
    CONF_CO2_HIGH,
    CONF_CO2_SENSOR,
    CONF_COMPRESSOR_SENSOR,
    CONF_CONTACTS,
    CONF_COOL_RELEASE_ABOVE,
    CONF_COOL_RELEASE_SWITCH,
    CONF_DRY_RUN,
    CONF_EXTRACT_TEMPERATURE_SENSOR,
    CONF_FAN_AIR_QUALITY,
    CONF_FAN_BOOST,
    CONF_FAN_HOLIDAY,
    CONF_FAN_NIGHT,
    CONF_FAN_NIGHT_COOLING,
    CONF_FAN_NORMAL,
    CONF_FAN_QUIET_MAX,
    CONF_FAN_SELECT,
    CONF_FORECAST_BLOCKS_ABOVE,
    CONF_FORECAST_ENTITY,
    CONF_FROST_PROTECTION_BELOW,
    CONF_FUNCTION_SELECT,
    CONF_HEAT_RELEASE_BELOW,
    CONF_HEAT_RELEASE_SWITCH,
    CONF_HUMIDITY_HIGH,
    CONF_HUMIDITY_SENSOR,
    CONF_NAME,
    CONF_NIGHT_END,
    CONF_NIGHT_START,
    CONF_NOTIFY_SERVICE,
    CONF_OPERATION_MODE_SELECT,
    CONF_OUTDOOR_SENSOR,
    CONF_PV_SENSOR,
    CONF_PV_SURPLUS_ABOVE,
    CONF_PV_TARGET_BOOST,
    CONF_RELEASE_HYSTERESIS,
    CONF_SUPPLY_TEMPERATURE_SENSOR,
    CONF_TARGET_COOL,
    CONF_TARGET_COOL_HOLIDAY,
    CONF_TARGET_COOL_WINDOW_OPEN,
    CONF_TARGET_HOLIDAY,
    CONF_TARGET_NIGHT,
    CONF_TARGET_NORMAL,
    CONF_TARGET_WINDOW_OPEN,
    CONF_TEMPERATURE_SENSOR,
    DEFAULTS,
    DOMAIN,
    SUBENTRY_TYPE_ROOM,
    TARGET_MAX,
    TARGET_MIN,
    ActuatorKind,
)
from .discovery import DiscoveredRoom, discover_rooms, discover_unit

TITLE = "Schwörer Climate Control"


def _entity(domain: str | list[str], **extra: Any) -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=domain, **extra)
    )


def _temperature(low: float = TARGET_MIN, high: float = TARGET_MAX) -> Any:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=low, max=high, step=0.1, unit_of_measurement="°C", mode="box"
        )
    )


def _stage() -> Any:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=0, max=4, step=1, mode="slider")
    )


def _suggest(key: str, values: Mapping[str, Any]) -> dict[str, Any]:
    """Pre-fill a field without making it a stored default."""
    value = values.get(key)
    return {} if value is None else {"suggested_value": value}


def _optional(schema: dict[Any, Any], key: str, values: Mapping[str, Any], field: Any) -> None:
    """Add a field that may be left empty, suggesting whatever is set now."""
    schema[vol.Optional(key, description=_suggest(key, values))] = field


def unit_schema(values: Mapping[str, Any]) -> vol.Schema:
    """The unit's own entities, plus the two optional extra inputs."""
    schema: dict[Any, Any] = {}
    required = {
        CONF_OUTDOOR_SENSOR: _entity("sensor", device_class="temperature"),
        CONF_FAN_SELECT: _entity("select"),
        CONF_HEAT_RELEASE_SWITCH: _entity("switch"),
        CONF_COOL_RELEASE_SWITCH: _entity("switch"),
        CONF_FUNCTION_SELECT: _entity("select"),
        CONF_COMPRESSOR_SENSOR: _entity("sensor"),
        CONF_OPERATION_MODE_SELECT: _entity("select"),
    }
    for key, field in required.items():
        schema[vol.Required(key, description=_suggest(key, values))] = field

    for key in (CONF_SUPPLY_TEMPERATURE_SENSOR, CONF_EXTRACT_TEMPERATURE_SENSOR):
        _optional(schema, key, values, _entity("sensor", device_class="temperature"))
    _optional(schema, CONF_BYPASS_SENSOR, values, _entity("sensor"))
    _optional(schema, CONF_FORECAST_ENTITY, values, _entity("weather"))
    _optional(schema, CONF_PV_SENSOR, values, _entity("sensor", device_class="power"))
    _optional(schema, CONF_NOTIFY_SERVICE, values, selector.TextSelector())
    schema[vol.Required(CONF_DRY_RUN, default=values.get(CONF_DRY_RUN, True))] = (
        selector.BooleanSelector()
    )
    return vol.Schema(schema)


def setup_schema(values: Mapping[str, Any], rooms_found: int) -> vol.Schema:
    """The setup form: the unit, and whether to take its rooms on at once.

    The rooms of a WGT hold nothing that cannot be discovered, so being asked
    about each of six in turn is six dialogs for no decision. The question is
    still asked, because creating six devices unannounced is the kind of thing
    that is annoying exactly once.
    """
    schema = dict(unit_schema(values).schema)
    if rooms_found:
        schema[vol.Required(CONF_ADD_ROOMS, default=True)] = selector.BooleanSelector()
    return vol.Schema(schema)


def room_subentries(rooms: list[DiscoveredRoom]) -> list[ConfigSubentryData]:
    """One room per thermostat of the unit, with what discovery can know.

    Contacts, humidity and CO2 belong to other integrations and cannot be
    guessed, so they stay empty and are added per room afterwards.
    """
    return [
        ConfigSubentryData(
            data={
                CONF_NAME: room.name,
                CONF_ACTUATOR: ActuatorKind.WGT_ROOM.value,
                CONF_CLIMATE_ENTITY: room.climate_entity,
            },
            subentry_type=SUBENTRY_TYPE_ROOM,
            title=room.name,
            unique_id=None,
        )
        for room in rooms
    ]


def thresholds_schema(values: Mapping[str, Any]) -> vol.Schema:
    """Everything the hub decides for the whole house."""
    merged = {**DEFAULTS, **values}
    schema: dict[Any, Any] = {}
    fields: dict[str, Any] = {
        CONF_TARGET_NORMAL: _temperature(),
        CONF_TARGET_NIGHT: _temperature(),
        CONF_TARGET_HOLIDAY: _temperature(),
        CONF_TARGET_WINDOW_OPEN: _temperature(),
        CONF_TARGET_COOL: _temperature(),
        CONF_TARGET_COOL_HOLIDAY: _temperature(),
        CONF_TARGET_COOL_WINDOW_OPEN: _temperature(),
        CONF_FROST_PROTECTION_BELOW: _temperature(),
        CONF_NIGHT_START: selector.TimeSelector(),
        CONF_NIGHT_END: selector.TimeSelector(),
        CONF_HEAT_RELEASE_BELOW: _temperature(-20, 30),
        CONF_RELEASE_HYSTERESIS: _temperature(0, 5),
        CONF_FORECAST_BLOCKS_ABOVE: _temperature(-20, 30),
        CONF_AUX_HEAT_BELOW: _temperature(-20, 30),
        CONF_COOL_RELEASE_ABOVE: _temperature(),
        CONF_FAN_NORMAL: _stage(),
        CONF_FAN_NIGHT: _stage(),
        CONF_FAN_HOLIDAY: _stage(),
        CONF_FAN_QUIET_MAX: _stage(),
        CONF_FAN_BOOST: _stage(),
        CONF_FAN_AIR_QUALITY: _stage(),
        CONF_FAN_NIGHT_COOLING: _stage(),
        CONF_HUMIDITY_HIGH: selector.NumberSelector(
            selector.NumberSelectorConfig(min=30, max=100, step=1, unit_of_measurement="%")
        ),
        CONF_CO2_HIGH: selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=400, max=3000, step=50, unit_of_measurement="ppm"
            )
        ),
        CONF_PV_SURPLUS_ABOVE: selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=15000, step=50, unit_of_measurement="W"
            )
        ),
        CONF_PV_TARGET_BOOST: _temperature(0, 5),
    }
    for key, field in fields.items():
        schema[vol.Required(key, default=merged[key])] = field
    return vol.Schema(schema)


def room_schema(values: Mapping[str, Any]) -> vol.Schema:
    """One room: what heats it, what measures it, and what it overrides."""
    schema: dict[Any, Any] = {
        vol.Required(CONF_NAME, description=_suggest(CONF_NAME, values)): (
            selector.TextSelector()
        ),
        vol.Required(
            CONF_ACTUATOR,
            default=values.get(CONF_ACTUATOR, ActuatorKind.WGT_ROOM.value),
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[kind.value for kind in ActuatorKind],
                translation_key=CONF_ACTUATOR,
            )
        ),
        vol.Required(
            CONF_CLIMATE_ENTITY, description=_suggest(CONF_CLIMATE_ENTITY, values)
        ): _entity("climate"),
    }
    _optional(
        schema,
        CONF_TEMPERATURE_SENSOR,
        values,
        _entity("sensor", device_class="temperature"),
    )
    _optional(
        schema,
        CONF_CONTACTS,
        values,
        _entity(["binary_sensor", "input_boolean"], multiple=True),
    )
    _optional(
        schema, CONF_HUMIDITY_SENSOR, values, _entity("sensor", device_class="humidity")
    )
    _optional(
        schema, CONF_CO2_SENSOR, values, _entity("sensor", device_class="carbon_dioxide")
    )

    # The overrides. Empty means the hub's value, which is what lets a decision
    # name the level a number came from.
    _optional(schema, CONF_TARGET_NORMAL, values, _temperature())
    _optional(schema, CONF_TARGET_NIGHT, values, _temperature())
    _optional(schema, CONF_TARGET_HOLIDAY, values, _temperature())
    _optional(schema, CONF_TARGET_WINDOW_OPEN, values, _temperature())
    _optional(schema, CONF_TARGET_COOL, values, _temperature())
    _optional(schema, CONF_FROST_PROTECTION_BELOW, values, _temperature())
    _optional(schema, CONF_NIGHT_START, values, selector.TimeSelector())
    _optional(schema, CONF_NIGHT_END, values, selector.TimeSelector())
    _optional(schema, CONF_AUX_HEAT_BELOW, values, _temperature(-20, 30))
    _optional(schema, CONF_HUMIDITY_HIGH, values, selector.NumberSelector(
        selector.NumberSelectorConfig(min=30, max=100, step=1, unit_of_measurement="%")
    ))
    _optional(schema, CONF_CO2_HIGH, values, selector.NumberSelector(
        selector.NumberSelectorConfig(min=400, max=3000, step=50, unit_of_measurement="ppm")
    ))
    schema[
        vol.Required(
            CONF_AUX_HEAT_OFF_AT_NIGHT,
            default=values.get(CONF_AUX_HEAT_OFF_AT_NIGHT, False),
        )
    ] = selector.BooleanSelector()
    return vol.Schema(schema)


#: The fields of each step, so that saving one step can replace exactly its own
#: keys. Both steps write to the same options dict, so a blind merge would
#: either wipe the other step or make a cleared field impossible to clear.
UNIT_KEYS: tuple[str, ...] = (
    CONF_OUTDOOR_SENSOR,
    CONF_FAN_SELECT,
    CONF_HEAT_RELEASE_SWITCH,
    CONF_COOL_RELEASE_SWITCH,
    CONF_FUNCTION_SELECT,
    CONF_COMPRESSOR_SENSOR,
    CONF_OPERATION_MODE_SELECT,
    CONF_SUPPLY_TEMPERATURE_SENSOR,
    CONF_EXTRACT_TEMPERATURE_SENSOR,
    CONF_BYPASS_SENSOR,
    CONF_FORECAST_ENTITY,
    CONF_PV_SENSOR,
    CONF_NOTIFY_SERVICE,
    CONF_DRY_RUN,
)

THRESHOLD_KEYS: tuple[str, ...] = tuple(thresholds_schema({}).schema)


def _prune(data: Mapping[str, Any]) -> dict[str, Any]:
    """Drop the fields that were left empty, so they resolve to the hub's value."""
    return {
        key: value
        for key, value in data.items()
        if value is not None and value != "" and value != []
    }


def _replace(
    current: Mapping[str, Any], user_input: Mapping[str, Any], keys: tuple[str, ...]
) -> dict[str, Any]:
    """Keep the other step's settings, replace this step's outright.

    Replacing rather than merging is what makes a field clearable: an optional
    field left empty is absent from the submitted data, and a merge would hand
    back the value the user had just removed.
    """
    kept = {key: value for key, value in current.items() if key not in keys}
    return {**kept, **_prune(user_input)}


class ClimateControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set the unit up once."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm the unit's entities, which are discovered where possible."""
        rooms = discover_rooms(self.hass)

        if user_input is not None:
            data = _prune(user_input)
            # Asked, not stored: it describes this one moment, not the setup.
            add_rooms = data.pop(CONF_ADD_ROOMS, False)
            return self.async_create_entry(
                title=TITLE,
                data=data,
                subentries=room_subentries(rooms) if add_rooms else None,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=setup_schema(discover_unit(self.hass), len(rooms)),
            description_placeholders={"rooms": str(len(rooms))},
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_TYPE_ROOM: RoomSubentryFlow}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ClimateControlOptionsFlow()


class ClimateControlOptionsFlow(OptionsFlow):
    """Change the unit's entities and the thresholds after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init", menu_options=["entities", "thresholds"]
        )

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data=_replace(self.config_entry.options, user_input, UNIT_KEYS)
            )
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="entities", data_schema=unit_schema(current))

    async def async_step_thresholds(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data=_replace(self.config_entry.options, user_input, THRESHOLD_KEYS)
            )
        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="thresholds", data_schema=thresholds_schema(current)
        )


class RoomSubentryFlow(ConfigSubentryFlow):
    """Add or change one room."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a room, suggesting the next one of the unit that has no entry."""
        if user_input is not None:
            data = _prune(user_input)
            if self._taken(data[CONF_CLIMATE_ENTITY]):
                return self.async_show_form(
                    step_id="user",
                    data_schema=room_schema(data),
                    errors={CONF_CLIMATE_ENTITY: "already_controlled"},
                )
            return self.async_create_entry(title=data[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="user", data_schema=room_schema(self._suggestion())
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            data = _prune(user_input)
            if self._taken(data[CONF_CLIMATE_ENTITY], excluding=subentry.subentry_id):
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=room_schema(data),
                    errors={CONF_CLIMATE_ENTITY: "already_controlled"},
                )
            return self.async_update_and_abort(
                self._get_entry(), subentry, title=data[CONF_NAME], data=data
            )

        return self.async_show_form(
            step_id="reconfigure", data_schema=room_schema(subentry.data)
        )

    def _taken(self, climate_entity: str, excluding: str | None = None) -> bool:
        """Whether another room already drives this thermostat.

        Two rooms on one thermostat would write the same setpoint from two
        decisions, and whichever ran last would win.
        """
        return any(
            subentry.data.get(CONF_CLIMATE_ENTITY) == climate_entity
            for subentry_id, subentry in self._get_entry().subentries.items()
            if subentry_id != excluding
        )

    def _suggestion(self) -> dict[str, Any]:
        """The first room of the unit that is not configured yet, if any."""
        taken = {
            subentry.data.get(CONF_CLIMATE_ENTITY)
            for subentry in self._get_entry().subentries.values()
        }
        for room in discover_rooms(self.hass):
            if room.climate_entity not in taken:
                return {
                    CONF_NAME: room.name,
                    CONF_CLIMATE_ENTITY: room.climate_entity,
                    CONF_ACTUATOR: ActuatorKind.WGT_ROOM.value,
                }
        return {}
