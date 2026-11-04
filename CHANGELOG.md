# Changelog

## Unreleased

### Added

- **The decisions say how close they are to changing.** Each decision sensor
  now lists the readings it watches with the limit that would turn it over and
  how far off that is (`thresholds`), what it already knows will happen and
  when (`upcoming`), and the entities behind its inputs (`sources`). None of it
  is recorded.
- **A dashboard that says what state the house is in, and why.** The strategy
  now builds the overview for the mode the controller runs in, from cards that
  ship with the integration: whether the system keeps up, energy, the heat
  pump, the auxiliary heaters, the air or cooling, each with how close the next
  change is. A page per room says why it is cool or warm; others cover the
  whole house being too cold or too warm, a chronicle of the last day, and the
  unit itself. The controls are gone from it: the controller runs on its own.
- **Power of the unit**, an optional entity under *Entities*. No decision reads
  it; the dashboard shows the energy from it.

## 1.5.0 - 2026-11-04

### Added

- **The setpoints and the night setback are entities.** Each room has a *Target
  temperature* and a *Target temperature at night*, and the hub a *Night
  setback* switch and a *Fan level at night* select. An automation can set them
  and the history shows when they changed. Each starts from what the
  configuration resolved to and holds its own value from then on, so the
  fields are gone from the room form and the fan field from the hub's. The
  hub's setpoints are what a new room starts from. With the night setback off
  the rooms keep their day setpoint at night, while the fan still runs its
  night stage.

### Changed

- **A restart no longer starts an auxiliary heater's wait over.** The 15 minutes
  a heater waits before it goes on used to begin again with every restart or
  reload, which in the living room meant twice in one morning. The room's
  decision sensor now records since when the heater has been waiting
  (`auxiliary_heat_waiting_since`), and the wait carries on from there when the
  record is less than 15 minutes old.

### Fixed

- **A contact that cannot be read counts as closed.** It used to count as an
  open window at once, and Zigbee contacts are unavailable for about a minute
  while Home Assistant starts, so every room they guard was set to 12 °C and
  back on each restart. A failed contact now leaves the heating alone. It is
  still listed under *Inputs missing* straight away, and a repair follows after
  an hour.

- **A slow device no longer raises "A value is not taken".** The counter behind
  it went up with every evaluation, including those while a write was held back
  by the one-minute spacing and those after the wanted value had changed. The
  unit takes most of a minute to read back, so a setpoint written and put back
  was reported as refused. Only a write sent again with the same value counts
  now.

## 1.6.0 - 2026-11-04

### Changed

- **A room has 30 minutes to rise, not 45.** A room warm supply air leaves to
  the heat pump now counts as not catching up after half an hour without
  rising by 0.2 K, and gets its heater 15 minutes later.

- **A restart no longer holds a room's heater back.** The watch on a room left
  to the heat pump used to start over with every restart of Home Assistant, so a
  room that was not warming waited a whole window again. Its first window now
  starts from the temperature the recorder saw half an hour earlier. A room
  whose heater is on at the time is still watched afresh.

## 1.4.1 - 2026-11-04

### Changed

- **A room that warm supply air does not warm gets its auxiliary heater.** Supply
  air well above the room used to leave it to the heat pump for as long as it
  stayed short of its setpoint. Now the room has to rise by 0.2 K within
  45 minutes. One that does not gets its heater after the usual 15 minutes, and
  keeps it until the room reaches its setpoint.

## 1.4.0 - 2026-11-03

### Added

- **The fan runs at least stage 3 while the heat pump heats.** The supply air
  leaves at the condenser temperature, so more air carries more of the
  compressor's heat. This applies by day only and while the mode is heating, and
  a room asking for more keeps its stage. The stage is set with *Fan level while
  the heat pump heats*.

## 1.3.0 - 2026-11-01

### Added

- **A repair names suggested entities that were never saved.** The entities
  form fills in discovered entities, while the controller works without them
  until the form is submitted once. A repair now points this out. Clearing the
  field declines the suggestion, and the repair does not come back for it.

### Fixed

- **Writes after a restart name the controller as their trigger.** The first
  write after a restart, and one putting back a value changed by hand, now log
  the decision behind them as "Restored: " followed by its sentence and show it
  as "triggered by". A restart that writes nothing logs nothing.

## 1.2.0 - 2026-10-31

### Added

- **Changes name the controller as their trigger.** A setpoint, release switch
  or fan level the controller sets now shows "triggered by" with the decision's
  name and sentence, in the logbook and in the entity's activity. A write with
  no logbook entry behind it, such as the first one after a restart, still
  shows none.

## 1.1.0 - 2026-10-22

### Added

- **The house-wide auxiliary heating release is driven.** Register 234 is on
  while any room may run its auxiliary heater and off once none may, written
  before the rooms are released and after they are withdrawn. Pick the entity
  under *Entities*; it is discovered for a new setup and suggested for an
  existing one.

### Changed

- **An auxiliary heater only runs when the room needs it.** It used to be
  released whenever it was cold enough outside. Now the room also has to be
  short of its setpoint, and the supply air (T4, after the reheater) has to be
  arriving too cool to warm it, with a dwell time on the way in and hysteresis
  on the way out. Three new thresholds, each overridable per room. Without a
  supply air sensor the room decides alone.

### Fixed

- **An entity chosen at setup can be cleared under *Entities*.** Clearing it
  used to leave the setup value in force. An entity cleared there is also not
  suggested again.

## 1.0.0 - 2026-10-03

### Added

- **Notify every change.** A debugging option that sends a message for every
  change of a system or room decision, not only when a release turns over.
  Each line is what the logbook gets, room lines start with the room's name.

### Changed

- **Releases are built by the release workflow.** It runs CI, bumps the
  version, dates this changelog and publishes the release. Start it from the
  Actions tab or with `gh workflow run release -f version=<version>`.
  `scripts/release.sh` is gone.

- **CI calls the shared workflows in josa42/actions.** They moved there from
  josa42/gha-workflows.

- **`make release` starts the release workflow.** It releases a minor version
  when a `feat` commit landed since the last release and a patch otherwise.
  Pass `VERSION=major`, `VERSION=minor`, `VERSION=patch` or `VERSION=1.2.3`
  to choose yourself. Without a release yet, it asks for the first version.
  It refuses to start while local changes are not pushed, since the workflow
  releases what is on GitHub.

- **The notification target is picked from the notify entities.** The field
  was free text for a notify service. A service set up that way still works.

### Fixed

- **Notifications reach a notify entity.** A target such as
  `notify.my_phone` was called as a service that does not exist, so nothing
  arrived. It now goes through `notify.send_message`, and a notification that
  cannot be sent is logged as a warning instead of failing silently.

## 0.2.0 - 2026-10-01

### Added

- Setup takes on every room of the unit at once. A room of a WGT holds nothing
  that cannot be discovered, so the form says how many it found and creates one
  per thermostat, with a checkbox that starts ticked. Contacts, humidity and CO₂
  sensors belong to other integrations and are added per room afterwards.
- The fan no longer ventilates against the heat. While it is warmer outside than
  the air leaving the house the level is capped, and past a larger excess the fan
  stops altogether, because a warm afternoon and a heat wave are not the same
  thing. This beats air quality: air at 39 °C carries far more water than room air
  at 23, so ventilating against indoor humidity on a hot day makes it worse.

### Changed

- Two rooms can no longer drive one thermostat. They would write the same
  setpoint from two decisions, and whichever ran last would win.
- The indicator for unreadable inputs is called "Inputs missing" rather than
  "Degraded", after what switches it on instead of after the consequence. The
  same list is now published under one name, `failed_inputs`, both there and on
  every decision sensor. The entity id follows the name, so the old entity stays
  behind as an orphan to delete once.
- Cooling with the compressor waits for energy the house has no better use for.
  It is the one expensive thing this controller can switch on, so it runs on
  surplus rather than on demand. The release lockout still wins on the way back
  out: losing the surplus does not stop a compressor that started less than half
  an hour ago, because short-cycling it is the worse outcome.
- One surplus input replaces the three PV fields, and drives both the cooling
  release and the setpoint boost. An on/off entity is taken at its word and acts
  at once; a number is read against a start and a stop threshold, the stop lower
  so that spending the surplus does not withdraw the reason for spending it.
  Production is not surplus, which the old field could not express: 2 kW under
  2 kW of load is nothing to spare. Existing entries are migrated rather than
  cleared.

### Fixed

- A room found through its thermostat rather than through its device was called
  "WGT - Wohnzimmer Raumthermostat". That name went on to be its device name, its
  entity id and every logbook entry about it.
- The subentry translations carried a `title` key that does not belong in them,
  so hassfest reported a warning once per translation file. `entry_type` already
  says what a room is, which is what that key was trying to do.

## 0.1.0 - 2026-10-01

### Added

- The decision engine. A pure function of inputs, configuration and previous
  state that decides both heat pump releases, the heating and cooling function,
  the fan level, and per room a setpoint and whether its heater may run. Three
  modes say which direction of energy is allowed, named after that rather than
  after the season, and holiday is a modifier on top of them.
- Frost protection, which forces heating as soon as a room falls below its limit,
  and keeps doing so when the outdoor reading has gone missing.
- Rooms the unit does not heat, through any `climate` entity, so a bathroom on a
  relay is configured the same way as a room of the WGT.
- Settings that resolve room, then hub, then default, with every decision naming
  the value it used and the level it came from.
- Write discipline. Only what differs from what the device reports is written,
  bundles are paced, and no bundle goes out within a minute of the last one. A
  dropped write is retried by itself and one that never takes is reported.
- A decision sensor for the unit and one per room, carrying the sentence, the
  inputs with their age, the conditions with their outcome and the settings with
  their source. A logbook entry on every change, so the history survives a
  restart.
- Repairs for the unit leaving manual mode, an input that has been unreadable for
  an hour, and a register that will not take its value.
- Notifications on a release turning over, gathered for five minutes.
- Diagnostics with the full trace and the writes it would send right now.
- A heat recovery sensor, which is how a bypass that moves no air is told apart
  from a controller that is not trying.
- Dry run, on for a fresh install.
