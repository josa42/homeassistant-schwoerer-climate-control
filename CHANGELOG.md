# Changelog

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
