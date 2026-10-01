# The v1 controller's configuration, as it was

Recovered on 2026-10-01 from the orphaned `schwoerer_wgt_controller` config
entry in Home Assistant, shortly before that entry was deleted. The
integration's code had already been removed, so the entry was the last copy of
these values and nothing else records them.

This is the configuration v1 actually ran with, not a proposal. It is here so
the thresholds this house was tuned to are not guessed at again, and so the room
mapping does not have to be rediscovered from the device.

## Thresholds

| Setting | Value |
| --- | --- |
| `outdoor_temp_heating_threshold` | 16 |
| `outdoor_temp_auxiliary_heating_threshold` | 10 |
| `co2_threshold` | 1000 |
| `co2_high_delay_minutes` | 5 |
| `humidity_threshold` | 70 |
| `test_mode` | true |

`outdoor_temp_heating_threshold` is the 16 degrees that
[design.md](design.md#heat-pump) describes the heat pump release as following,
which is where the hysteresis and the 30-minute stability lockout now apply.

`test_mode` was left on. Whatever it did in v1, the house was being driven by
the hand-written `automation.heizung` rather than by the controller, so these
thresholds were configured but not necessarily proven in anger.

## Rooms

The `room_N` keys match the WGT's own room numbering exactly, confirmed against
the `room_number` attribute each climate entity reports. Note that Kinderzimmer
1 and 2 are **not** in numeric order: Kinderzimmer 2 is room 5 and Kinderzimmer
1 is room 6. Anything that assumes the names and the indices agree will write
the wrong room's register.

| Room | Name in v1 | Bedroom | Window sensor |
| --- | --- | --- | --- |
| 1 | Wohnzimmer | no | `binary_sensor.wohnzimmer_fenster_contact` |
| 2 | `" Windfang"` | no | `binary_sensor.haustur_contact` |
| 3 | Arbeitszimmer | no | `binary_sensor.arbeitszimmer_fenster_contact` |
| 4 | Schlafzimmer | yes | `binary_sensor.schlafzimmer_fenster_contact` |
| 5 | Kinderzimmer 2 | yes | `binary_sensor.kinderzimmer_2_fenster_contact` |
| 6 | Kinderzimmer 1 | yes | `binary_sensor.kinderzimmer_1_fenster_contact` |

Only room 1 carried a CO₂ sensor:
`sensor.alpstuga_air_quality_monitor_kohlendioxid`.

Two details that are easy to read as mistakes and are not. Room 2's name is
stored with a **leading space**, `" Windfang"`. Room 2's window sensor is the
front door contact, because the Windfang is the entrance hall and the door is
what opens.

## The climate entity IDs in that config were stale

v1 stored a `climate_entity_id` per room, and **every one of them had already
stopped resolving**. The entities gained an area prefix at some point after the
controller was configured, so the stored IDs point at nothing:

| Stored in v1 (does not exist) | Actual entity today |
| --- | --- |
| `climate.wgt_wohnzimmer_raumthermostat` | `climate.wohnzimmer_wgt_wohnzimmer_raumthermostat` |
| `climate.wgt_windfang_raumthermostat` | `climate.windfang_wgt_windfang_raumthermostat` |
| `climate.wgt_arbeitszimmer_raumthermostat` | `climate.arbeitszimmer_wgt_arbeitszimmer_raumthermostat` |
| `climate.wgt_schlafzimmer_raumthermostat` | `climate.schlafzimmer_wgt_schlafzimmer_raumthermostat` |
| `climate.wgt_kinderzimmer_2_raumthermostat` | `climate.kinderzimmer_2_wgt_kinderzimmer_2_raumthermostat` |
| `climate.wgt_kinderzimmer_1_raumthermostat` | `climate.kinderzimmer_1_wgt_kinderzimmer_1_raumthermostat` |

Checked by lookup: `climate.wgt_wohnzimmer_raumthermostat` answers
`ENTITY_NOT_FOUND`. The right-hand column was read from the live entity
registry and carries the matching `room_number`.

This is worth more than a correction. A stored entity ID that silently stops
resolving is the same class of failure as a write that silently does not arrive,
and v1 had no way to say either had happened. It is an argument for resolving
rooms by the device's own room number and treating the entity ID as a lookup
that can fail loudly.

## Sensors that were unavailable when this was captured

- `binary_sensor.haustur_contact` (room 2's window sensor)
- `sensor.alpstuga_air_quality_monitor_kohlendioxid` (room 1's CO₂ sensor)

Both existed in the registry and reported `unavailable`, which is a different
thing from the climate IDs above: these resolve, they just had no value at that
moment. [design.md](design.md#sensor-failure) covers what the controller should
do with a sensor in that state, and these two are the ones that will exercise it
first.
