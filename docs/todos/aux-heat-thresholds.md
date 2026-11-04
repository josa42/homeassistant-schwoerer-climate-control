# Tune the auxiliary heater thresholds against real data

The auxiliary heater decision has three thresholds and a dwell time that are
first estimates, not measurements:

| Setting | Default | What it decides |
| --- | --- | --- |
| `aux_supply_margin` | 5 K | Supply air at least this much warmer than the room counts as the heat pump warming it |
| `aux_deficit` | 0.5 K | How far below its setpoint a room has to be before the heater is considered |
| `aux_deficit_override` | 2 K | From this far below the setpoint the supply air no longer gets a say |
| `AUX_DWELL` | 15 min | How long the heater has to be wanted before it is switched on |
| `AUX_PROGRESS_WINDOW` | 45 min | How long a room left to the heat pump gets to rise |
| `AUX_PROGRESS_MIN_RISE` | 0.2 K | How much it has to rise in that window |

The margin is the one that matters. It rests on a back-of-the-envelope figure:
30 to 40 m³/h into a room at 5 K above it is roughly 50 to 70 W, which is too
little to lift a room that is a kelvin short in any reasonable time. Nothing has
checked that against this house.

The first cold morning showed that the margin alone cannot tell the two apart.
On 4 November at 4 °C outside, with the compressor running and the fan at
stage 3, the supply air sat at 41 °C, 22 K above the living room, from 05:00 to
09:00. The room went from 19.1 °C to 19.4 °C and back to 18.9 °C. The margin
said "catching up" the whole time. That is why the room now has to show it, by
rising within a window. The margin is still the quick test for a heat pump
that brings nothing, and the window is the test for one that brings too little.

T4 itself is the right sensor. The auxiliary heaters sit in the rooms, after T4,
so it reads what the ventilation delivers without their heat.

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
- A progress window and rise that call a slow but steady room catching up and
  a stuck one stalled. 0.2 K is two steps of a sensor that reads in tenths, so
  the window cannot get much shorter without the noise deciding.
- Whether 15 minutes outlasts a defrost. If the supply air dips for longer, the
  dwell has to grow or a defrost has to be recognised on its own.
- Whether the override is wanted, or comfort should always wait for the supply
  air.

Thresholds belong in `DEFAULTS` in `const.py` once settled; the dwell is a
constant there too. Then drop this file and the README pointer to it.
