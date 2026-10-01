"""Tests for setting the controller up, and for what a room inherits."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.schwoerer_climate_control.const import (
    CONF_CLIMATE_ENTITY,
    CONF_DRY_RUN,
    CONF_FAN_SELECT,
    CONF_NAME,
    CONF_OUTDOOR_SENSOR,
    CONF_TARGET_NORMAL,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
    SUBENTRY_TYPE_ROOM,
)
from custom_components.schwoerer_climate_control.discovery import (
    discover_rooms,
    discover_unit,
)

from .conftest import HUB_DATA, OUTDOOR


async def test_setting_the_unit_up(hass: HomeAssistant, unit) -> None:
    unit()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], HUB_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_OUTDOOR_SENSOR] == OUTDOOR


async def test_only_one_controller_per_unit(hass: HomeAssistant, entry, unit) -> None:
    unit()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_an_omitted_field_is_not_stored(hass: HomeAssistant, unit) -> None:
    # An entity selector rejects both None and an empty string, so a field left
    # empty arrives absent. Absent is also what has to be stored: it is what
    # resolves to the hub's value and lets a decision name the level it came from.
    unit()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], dict(HUB_DATA)
    )
    assert "forecast_entity" not in result["data"]
    assert "pv_sensor" not in result["data"]


async def test_a_cleared_text_field_is_not_stored(hass: HomeAssistant, unit) -> None:
    # The notification service is free text rather than an entity, so clearing it
    # really does arrive as an empty string.
    unit()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**HUB_DATA, "notify_service": ""}
    )
    assert "notify_service" not in result["data"]


async def test_adding_a_room(hass: HomeAssistant, entry, unit, setup_entry) -> None:
    unit()
    await setup_entry(entry)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_ROOM), context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Badezimmer",
            "actuator": "generic",
            CONF_CLIMATE_ENTITY: "climate.badezimmer",
            CONF_TARGET_NORMAL: 22.0,
            "aux_heat_off_at_night": False,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Badezimmer"
    assert result["data"][CONF_TARGET_NORMAL] == 22.0
    assert CONF_TEMPERATURE_SENSOR not in result["data"]


async def test_discovery_finds_the_unit(hass: HomeAssistant) -> None:
    # Every entity of the ventilation integration publishes its translation key
    # as entity_type, which is what discovery reads.
    hass.states.async_set(
        "sensor.wgt_outdoor", "7.5", {"entity_type": "temperature_t10_outdoor"}
    )
    hass.states.async_set("select.wgt_fan", "2", {"entity_type": "fan_speed"})
    found = discover_unit(hass)
    assert found[CONF_OUTDOOR_SENSOR] == "sensor.wgt_outdoor"
    assert found[CONF_FAN_SELECT] == "select.wgt_fan"


async def test_discovery_skips_a_rooms_copy_of_an_entity(hass: HomeAssistant) -> None:
    hass.states.async_set(
        "sensor.room_1_outdoor",
        "7.5",
        {"entity_type": "temperature_t10_outdoor", "room_number": 1},
    )
    assert CONF_OUTDOOR_SENSOR not in discover_unit(hass)


async def test_discovery_finds_the_rooms_in_order(hass: HomeAssistant) -> None:
    for number, name in ((2, "Schlafzimmer"), (1, "Wohnzimmer")):
        hass.states.async_set(
            f"climate.wgt_room_{number}",
            "fan_only",
            {
                "entity_type": "climate_room",
                "room_number": number,
                "friendly_name": f"WGT - {name} Raumthermostat",
            },
        )
    rooms = discover_rooms(hass)
    assert [room.number for room in rooms] == [1, 2]
    assert rooms[0].climate_entity == "climate.wgt_room_1"


async def test_an_optional_field_can_be_cleared_again(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    # Merging the submitted data over the stored options would hand back the
    # value the user had just removed, because an empty field is absent rather
    # than empty.
    unit()
    hass.config_entries.async_update_entry(
        entry, options={"pv_sensor": "sensor.pv", CONF_TARGET_NORMAL: 21.0}
    )
    await setup_entry(entry)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "entities"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], HUB_DATA
    )

    assert "pv_sensor" not in result["data"], "a cleared field has to stay cleared"
    assert result["data"][CONF_TARGET_NORMAL] == 21.0, "the other step survives"


async def test_a_room_is_named_after_the_room_and_not_the_thermostat(
    hass: HomeAssistant,
) -> None:
    # A device is called "WGT - Wohnzimmer" and its thermostat "WGT - Wohnzimmer
    # Raumthermostat". Neither spelling is what the room is called, and the
    # name ends up on the device, the entity id and every logbook entry.
    hass.states.async_set(
        "climate.wgt_room_1",
        "fan_only",
        {
            "entity_type": "climate_room",
            "room_number": 1,
            "friendly_name": "WGT - Wohnzimmer Raumthermostat",
        },
    )
    assert discover_rooms(hass)[0].name == "Wohnzimmer"


async def test_a_room_with_no_name_at_all_still_gets_one(hass: HomeAssistant) -> None:
    hass.states.async_set(
        "climate.wgt_room_4", "fan_only", {"entity_type": "climate_room", "room_number": 4}
    )
    assert discover_rooms(hass)[0].name == "Room 4"


async def test_the_dry_run_default_is_on(hass: HomeAssistant, unit) -> None:
    unit()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    schema = result["data_schema"]({**HUB_DATA, CONF_DRY_RUN: True})
    assert schema[CONF_DRY_RUN] is True


def fake_wgt_rooms(hass: HomeAssistant, *names: str) -> None:
    """Thermostats of the unit, as the ventilation integration reports them."""
    for number, name in enumerate(names, start=1):
        hass.states.async_set(
            f"climate.wgt_room_{number}",
            "fan_only",
            {
                "entity_type": "climate_room",
                "room_number": number,
                "friendly_name": f"WGT - {name} Raumthermostat",
            },
        )


async def test_setup_takes_on_every_room_of_the_unit(
    hass: HomeAssistant, unit
) -> None:
    # A WGT room holds nothing that cannot be discovered, so being asked about
    # each of six in turn is six dialogs for no decision.
    unit()
    fake_wgt_rooms(hass, "Wohnzimmer", "Schlafzimmer", "Arbeitszimmer")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert "3" in result["description_placeholders"]["rooms"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**HUB_DATA, "add_rooms": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    rooms = list(result["subentries"])
    assert [room["title"] for room in rooms] == [
        "Wohnzimmer",
        "Schlafzimmer",
        "Arbeitszimmer",
    ]
    assert rooms[0]["data"][CONF_CLIMATE_ENTITY] == "climate.wgt_room_1"
    assert rooms[0]["data"]["actuator"] == "wgt_room"
    assert "add_rooms" not in result["data"], "the question is not a setting"


async def test_setup_can_decline_the_rooms(hass: HomeAssistant, unit) -> None:
    unit()
    fake_wgt_rooms(hass, "Wohnzimmer")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**HUB_DATA, "add_rooms": False}
    )
    assert list(result["subentries"]) == []


async def test_the_rooms_arrive_as_devices(hass: HomeAssistant, unit) -> None:
    unit()
    fake_wgt_rooms(hass, "Wohnzimmer", "Schlafzimmer")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.config_entries.flow.async_configure(
        result["flow_id"], {**HUB_DATA, "add_rooms": True}
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.wohnzimmer_decision") is not None
    assert hass.states.get("sensor.schlafzimmer_decision") is not None


async def test_one_thermostat_cannot_be_driven_by_two_rooms(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    # Two rooms on one thermostat would write the same setpoint from two
    # decisions, and whichever ran last would win.
    unit()
    await setup_entry(entry)

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_ROOM), context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Noch mal Wohnzimmer",
            "actuator": "wgt_room",
            CONF_CLIMATE_ENTITY: "climate.wohnzimmer",
            "aux_heat_off_at_night": False,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_CLIMATE_ENTITY: "already_controlled"}


async def test_a_room_may_keep_its_own_thermostat_when_reconfigured(
    hass: HomeAssistant, entry, unit, setup_entry
) -> None:
    unit()
    await setup_entry(entry)
    subentry_id = next(iter(entry.subentries))

    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_TYPE_ROOM),
        context={"source": "reconfigure", "subentry_id": subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Wohnzimmer",
            "actuator": "wgt_room",
            CONF_CLIMATE_ENTITY: "climate.wohnzimmer",
            CONF_TARGET_NORMAL: 21.5,
            "aux_heat_off_at_night": False,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry_id].data[CONF_TARGET_NORMAL] == 21.5
