# Design: Schwörer Climate Control

This document records the decisions this integration is built from, and the
reasoning behind them. It is the answer to "why is it built this way", which in
six months is as hard to reconstruct as "why is the auxiliary heater on".

Repository `homeassistant-schwoerer-climate-control`, domain
`schwoerer_climate_control`.

## Why v1 is being replaced

The symptom was that written values did not arrive. The cause is in the write
path, not in the logic.

v1 wrote around 15 fields on every evaluation: six room setpoints, six HVAC
modes, the fan level and two switches. It wrote all of them unconditionally,
without checking whether any had changed, and it evaluated not only every 15
minutes but on every state change of every window, humidity and CO₂ sensor it
watched. Its own coordinator debounces that to one evaluation per 10 seconds, so
sustained sensor traffic meant about 1.5 Modbus writes per second against a
device that is also polled in full every 30 seconds.

`schwoerer_lueftung` additionally triggers a full device poll after each field it
writes (`coordinator.py`, `async_write`), which amplifies a burst. Less than it
appears: it passes no debouncer of its own, so the default applies, a 10 second
cooldown with `immediate=True`, and `Debouncer._async_schedule_or_call_now` only
sets a flag while that timer runs. A burst inside one cooldown therefore costs
one immediate poll and one trailing one rather than one per write. The volume of
writes is the problem, and the amplification makes it worse.

Writing unconditionally is what turned a controller into a load generator, so
writing only what differs is the fix that matters. See Write discipline below for
what that leaves to do.

Two further defects from v1, fixed independently of that:

`DEFAULT_HEAT_PUMP_CHANGE_LOCKOUT_MINUTES = 30` was defined in `const.py` and
used nowhere. The hand-written `automation.heizung` implements that lockout and
v1 lost it, so the heat pump release could flip as often as the outdoor
temperature crossed the threshold.

There was no hysteresis at all. `outdoor_temp < threshold` decides afresh on
every evaluation when the reading sits near the threshold.

## Scope

The integration drives a Schwörer WGT through the entities of
`schwoerer_lueftung`, and can additionally serve rooms the WGT does not heat.

It is deliberately vendor specific. One fan level for all rooms, a heat pump
release with compressor protection, auxiliary heat per room through `hvac_mode`,
an operating mode that has to sit on `manual`, and a bypass that can only be
read. None of these concepts exist in a generic climate controller.

Reuse comes from the layering, not from the name. The engine is vendor neutral
and free of Home Assistant imports, and the device knowledge sits in adapters. An
air conditioner is a later adapter rather than a rewrite.

## Architecture

| Part | Responsibility |
| --- | --- |
| `engine.py` | Pure function of inputs, config and time, returning a decision. No HA import, no writing. |
| `models.py` | `Decision`, `Gate`, `EffectiveConfig`, `Setting`. Every setting carries its value and its origin. |
| `adapters/schwoerer.py` | Knows the fan level, heat pump release, auxiliary heat, heating/cooling function and shock ventilation. |
| `adapters/generic.py` | Knows one `climate` entity: a target temperature and heat or off. |
| `coordinator.py` | Schedules evaluations, diffs, bundles writes, enforces the rate cap, publishes decisions. |

The pattern is taken from `cover-control`, where separating pure geometry from the
Home Assistant plumbing has held up well.

## Write discipline

Protection against overloading Modbus sits on two layers with separate
responsibilities. Transport safety belongs to `schwoerer_lueftung`, because that
is where the connection lives and because every other writer benefits, the UI and
hand-written scripts included. Discipline about intent belongs to the controller.

The controller half is not waiting on the other one. Diffing removes almost all
of the traffic by itself: in a steady state the controller writes no register at
all, and what is left are real transitions. Pacing inside a bundle is the
controller's own to do. And because the diff compares against what the device
reports rather than against what the controller believes it sent, a dropped write
is retried on the next evaluation without anything extra being built, and a
register that never holds its value can be counted and reported.

What the lower layer adds, and the controller cannot, is protection against other
writers. A dashboard card, a script or a hand on the thermostat still reaches the
device unmetered, and a concurrent write from the UI can undo the controller's
pacing. That makes the queue worth having rather than a precondition.

In `schwoerer_lueftung` (separate repository, separate piece of work):

| Measure | Reason |
| --- | --- |
| Serialized write queue | Never two writes at once on one Modbus connection. |
| Minimum spacing between writes | The device needs time between register accesses. |
| Coalescing per field | Of three writes to the same register within a second, only the last one matters. |
| Readback verification with retry | A silently dropped write is precisely what made v1 unusable. |
| No poll per write | One poll after the queue drains is enough. |

In the controller:

| Measure | Reason |
| --- | --- |
| Write diffs only | What already holds needs no write. |
| One bundle per decision | Not per rule, not per room. |
| 30 s debounce on state changes | A window contact that chatters causes one evaluation, not eight. |
| At least 60 s between bundles | A ceiling on the load regardless of how many triggers fire. |
| Additionally every 15 minutes | So time boundaries such as the night setback take effect without a trigger. |

## Controls

Everything central hangs off the hub device. A room has only its decision sensor,
because the fan level is central anyway and selective intervention goes through
the central controls.

| Entity | Values | Meaning |
| --- | --- | --- |
| `switch` Active | on, off | Off writes nothing at all. The unit keeps running on its last values and the decision sensors keep showing what it would do. |
| `switch` Dry run | on, off | Everything is evaluated and published, nothing is written. On for a first install. |
| `select` Mode | heating, ventilation, cooling | Which direction of energy is allowed, not what is currently running. |
| `switch` Holiday | on, off | A modifier on the mode rather than a mode of its own. |
| `select` Fan | automatic, quiet, boost, 0 to 4 | Modes and fixed stages in one select, the way the device's own select is built. |
| `sensor` Decision (hub) | intent | The central decision, with inputs, gates and settings as attributes. |
| `sensor` Decision (per room) | intent | The same for one room. |
| `binary_sensor` Degraded | on, off | At least one configured input is missing. |

The device's `Betriebsart` stays on `manual` and is only read. If it reads
anything else the controller raises a repair rather than fighting it. Two
automations overwriting each other are the reason "why is X on" becomes
unanswerable. Research in the `schwoerer_lueftung` repository
(`docs/research/001-bypass-control.md`) confirms that `manual` costs nothing:
over a week with more than a hundred damper transitions, `Betriebsart` gated
none of them.

## Mode as a direction of energy

The mode is not named after the calendar. It is heating, ventilation or cooling,
and that has three consequences, all of them wanted.

The name says which gate is open instead of asserting a season. Summer in April
is wrong, ventilation in April is right.

It maps one to one onto register 230, the heating/cooling function, which the
controller writes. There is no translation table that can drift.

Ventilation is a safe fallback. Neither heating nor cooling means the base
function keeps running. On sensor failure or contradiction the controller falls
back there, which is never wrong, only sometimes not optimal.

No rule ever branches on the mode itself. Each rule reads its own gate with its
own reason, and the mode is one input to that gate. Automating the switch later is
therefore a change of source and not a change to the logic. The decision record
already carries what such an automation needs: a multi-day rolling mean of the
outdoor temperature, the forecast and the cooling potential. The instantaneous
reading alone will not do, since T10 read 20.9 °C in early October.

## Resolving settings

Every setting is resolved in the order room, hub, default, using absolute values
rather than offsets. That holds for setpoints, times, thresholds and flags alike.
An offset composes badly: whether it should also apply to the holiday value and to
the window-open temperature is sometimes right and sometimes nonsense, and the
answer would have to be hard-coded.

Every decision names, for each setting it used, the value and the source. "Target
18.5 °C (source room), night starts 20:00 (source hub)" answers the question
without comparing two configuration dialogs.

Auxiliary heat off at night is a room field in the same mechanism rather than a
floor construct. In a house whose bedrooms happen to be the upper floor this
produces the same behaviour, and it stays correct when that stops being true.

## Rooms

A room is a name, a current temperature, zero or more opening contacts, optionally
humidity and CO₂, and exactly one actuator: a `climate` entity.

For the WGT rooms that is the room thermostat, whose `hvac_mode` switches the
auxiliary heater. For rooms the WGT does not heat it is any other `climate`
entity, so a radiator valve or a `generic_thermostat` in front of a relay.

The controller does not regulate a relay itself. Hysteresis, minimum run time and
minimum rest are things `generic_thermostat` has been getting right for years, and
self-written safety-critical control is exactly the class of code that did the
damage in v1. The price is one helper per relay room, created by hand.

Zero opening contacts is a valid state. Not every room has one.

## Heat pump

The release follows the outdoor temperature with hysteresis around the threshold,
and it is only changed when it has been stable for at least 30 minutes or the heat
pump is not currently running. Both are taken from `automation.heizung`, where
they have proven themselves, and both were missing in v1.

In cooling mode the same lockout applies to the cooling release. The cheapest path
wins: night cooling through the fan level first, and the heat pump release only
when that is not enough.

## Cooling and the bypass

The bypass is register 123 and read only. There is no write register for it on any
known firmware, and the damper is driven by the unit's own controller. What the
controller here can reach are the inputs that decision is made from, which is as
close as this interface gets. Measurements are in
`docs/research/001-bypass-control.md` in the `schwoerer_lueftung` repository.

Three of those inputs are reachable, and two of them the controller writes anyway:

| Input | How it is reached |
| --- | --- |
| Heating/cooling function must be Kühlen | Register 230, written by the mode. Leaving Kühlen closes the damper within seconds. |
| Room setpoint below the room temperature | The room's target temperature. This is the cooling demand the unit looks for. |
| Fan stage above 0 | Stage 0 closes the damper. Cooling therefore never asks for stage 0. |

This makes the cooling setpoint do double duty, and it is the same number either
way. In cooling mode a room's target means "cool down to this", and a target below
the current temperature is both the expression of that intent and the condition
that opens the bypass. Nothing extra has to be written to steer the damper.

Two limits cannot be reached. The unit gates the bypass with a lower limit on the
outdoor temperature, measured at 10 °C over three independent occurrences, and no
register for that parameter is identified, so it can be neither read nor changed.
And which indoor temperature the outdoor temperature is compared against is
undecided, with room 1 the likely candidate.

The controller therefore treats the bypass as an observation. It reads register
123, it knows the conditions, and it reports when the damper is closed while
cooling is wanted. Reporting is the action.

### The bypass path on this unit carries no air

This is the part that limits what cooling can achieve here, and it is a hardware
finding rather than a software one.

Across two weeks of history there is no hour in which the supply air departed
from full heat recovery. Restricted to hours with the fan running and at least
5 K between outdoor and extract air, the recovery implied by
`(T3 - T10) / (T5 - T10)` is 0.88 to 0.96 while register 123 reports open, and
0.89 while it reports closed. There is no difference, including 36 consecutive
hours reported open at a 12 K gradient and a night at 15 K. The owner reports that
the flap is audible, which rules out a dead servo and a unit built without the
option, and locates the fault in the bypass path rather than in the actuator or
the register.

Until that is found, night cooling on this unit cools nothing: air drawn in at
night is returned to indoor temperature by the exchanger on its way through.
Raising the fan level still exchanges air, which is worth having for humidity and
CO₂, but it is not a cooling lever here.

Two things follow for the design. Cooling is built as specified, because the
decision logic is correct and the fault is downstream of it. And the integration
publishes the effectiveness it measures, so that a bypass that starts working is
visible immediately and one that does not cannot be mistaken for a controller
that is not trying.

## Fan level

The fan level is central. Humidity and CO₂ are measured per room but feed a single
decision, which names the room that is asking and the stage it asks for.

Air quality wins, at night too. Seventy-eight percent in the bathroom over eight
hours is a mould risk, and that is more expensive than a stage of noise. Anyone
who wants it otherwise switches the fan mode to `quiet`, which applies a
configurable ceiling and says in every decision that it capped the result.
`boost` raises it the same way. Both hold until they are switched, and an
expiry can be added later.

Rooms with an open window ask for nothing. Their humidity and CO₂ readings are
measuring outdoors.

## Sensor failure

A failure is never silent and never makes a rule quietly disappear. v1 did
`if not state: continue` everywhere, which made a dead CO₂ sensor mean good air
and a dead window contact mean a closed window.

| Input | On failure |
| --- | --- |
| Opening contact | Counts as open. Better not to heat than to heat against an open window. |
| Outdoor temperature | Last valid value up to a maximum age, then fall back to ventilation. |
| A room's current temperature | The room keeps its setpoint and the auxiliary heater stays off. |
| Humidity, CO₂ | The rule drops out for that room, visibly in the record. |
| Forecast, PV | The refinement drops out, the base rule stands. |

Alongside that a `binary_sensor` Degraded, and a repair entry when a configured
input has been missing for longer than a threshold. Every input appears in the
decision record with its value, its age and its validity.

## Transparency

"Why is the auxiliary heater on" is usually a question about the past, and the
answer has to survive a restart and eight hours.

The current state lives in the attributes of the decision sensor: the inputs with
age and validity, the gates with their outcome, the settings with their source,
and a finished sentence. The large attributes are excluded from the recorder,
because six rooms every 15 minutes would otherwise fill the database.

The history lives in the logbook. Every change of a decision writes an entry with
that finished sentence, per room and for the hub. "Why was it on at three in the
morning" is then a look at the room's logbook.

On top of that a diagnostics download for the full snapshot, and a dashboard
strategy with an overview and a debug view, as in `cover-control`.

Notifications go to one `notify` service and are gathered for five minutes, so a
switch that affects six rooms is one message instead of six. A change of the heat
pump release is reported, which is what `automation.heizung` does today.

## Extra inputs in v1

| Input | Effect |
| --- | --- |
| Weather forecast | The day's maximum instead of the instantaneous reading for the heat pump release, the trigger for night cooling in cooling mode, and later an input to automating the mode. |
| PV surplus | Raise setpoints or release auxiliary heat while a surplus is available. The reason has to explain why it is 21.5 rather than 20.0 °C. |
| Door contacts | Fed into the same window-open logic, several contacts per room. |

Holiday stays a manual switch. Automating it is something Home Assistant can do,
as it does today.

## Decided against

The controller always wins. There is no detection of manual intervention and no
override state that could get stuck. Turning the room thermostat by hand therefore
has no lasting effect, and that is the price of the controller's state being fully
determined by its configuration and its readings.

There are no boost buttons and no per-room enable switches, only the central
controls. A room that should permanently differ gets its setting changed.

Mode and holiday are two axes rather than one flat list. A holiday in January
needs frost protection and reduced setpoints, one in July needs neither. As an
exclusive fourth mode, holiday would still have to know the season, and that
hidden branch is where reasons go missing.

The name carries the vendor. A generic name would be a promise the code does not
keep, and it would turn every WGT peculiarity into a special case that ought to be
abstracted away one day. This way the same peculiarity is the declared subject.

No schedule helpers per room. Night start and night end run through the same
resolution mechanism as everything else. Maintaining six schedules whose reasons
point at foreign entities costs more than two numbers per room.

## Not in v1

Automating the mode switch. The data sources are carried, the switch stays manual.
Switching is expensive, so it needs a dead band and a dwell time measured in days,
and that wants watching before it runs on its own.

Presence and calendar as inputs. A phone in flight mode that lowers the heating
while somebody is at home is a poor trade for a switch that works.

The unit's error and filter messages, electricity price and grid carbon intensity,
an adapter for air conditioners.

## Open questions

Why the bypass channel carries no air. This is a hardware question and it caps
what cooling can do on this unit, but it does not change the decision logic.

Which indoor temperature the unit compares the outdoor temperature against.
Room 1 is the likely candidate because the setpoint condition turned out to be
room 1's, but that is an inference. It matters for how accurately the integration
can predict the damper, not for what it writes.

What the bypass does on the heating side. Register 123 reports a state 2 for
"open for heating" that has never been observed, and every threshold measured so
far comes from the cooling side.
