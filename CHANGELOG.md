# Changelog

## Unreleased

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
