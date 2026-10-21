# Tune the auxiliary heater thresholds against real data

The auxiliary heater decision has three thresholds and a dwell time that are
first estimates, not measurements:

| Setting | Default | What it decides |
| --- | --- | --- |
| `aux_supply_margin` | 5 K | Supply air at least this much warmer than the room counts as the heat pump warming it |
| `aux_deficit` | 0.5 K | How far below its setpoint a room has to be before the heater is considered |
| `aux_deficit_override` | 2 K | From this far below the setpoint the supply air no longer gets a say |
| `AUX_DWELL` | 15 min | How long the heater has to be wanted before it is switched on |

The margin is the one that matters. It rests on a back-of-the-envelope figure:
30 to 40 m³/h into a room at 5 K above it is roughly 50 to 70 W, which is too
little to lift a room that is a kelvin short in any reasonable time. Nothing has
checked that against this house.

## What to look at

Over a few cold days with the heat pump released and dry run on:

- **T4 after the reheater** (`temperature_t4_after_reheater`) while the compressor
  runs, while it stands still, and through a defrost. How far above the rooms
  does it sit, and how long do the dips last?
- **Room temperature against setpoint** for the rooms with an auxiliary heater.
  How fast does a room recover on the heat pump alone at a given T4 lift?
- **The decision sensors**. Every room records `aux_room_below_target`,
  `aux_supply_insufficient` and `aux_dwell` with their numbers, so the logbook
  says how often the heater would have run and why.

## What to decide

- A margin that separates "catching up" from "not getting anywhere", read off
  the recovery rate against the T4 lift.
- Whether 15 minutes outlasts a defrost. If the supply air dips for longer, the
  dwell has to grow or a defrost has to be recognised on its own.
- Whether T4 is the right sensor at all. It assumes the room's auxiliary heater
  sits downstream of T4, so that T4 is what the heat pump alone delivers. If it
  is upstream, T4 includes the heater's own heat and the test holds itself on.
- Whether the override is wanted, or comfort should always wait for the supply
  air.

Thresholds belong in `DEFAULTS` in `const.py` once settled; the dwell is a
constant there too. Then drop this file and the README pointer to it.
