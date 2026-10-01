# Schwörer Climate Control

[![License](https://img.shields.io/github/license/josa42/homeassistant-schwoerer-climate-control?style=flat-square)](LICENSE)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://hacs.xyz/)

A Home Assistant integration that decides what a Schwörer WGT should do, and can
always tell you why it decided that.

It sits on top of the
[schwoerer_lueftung](https://github.com/josa42/homeassistant-schwoerer-lueftung)
integration, which talks Modbus to the device. This one owns the decisions: room
setpoints, when the heat pump is released, which rooms get auxiliary heat, and
what the fan level should be. Rooms the WGT does not heat can join in through any
`climate` entity.

> [!WARNING]
> This is built for one house. The logic, the defaults and the opinions are the
> author's own, and nothing here tries to be a general-purpose climate
> controller. Use it as a starting point, not as a product.

> [!NOTE]
> Nothing is released yet. The decisions it is built from, and the reasoning
> behind them, are written down in [docs/design.md](docs/design.md).

<br><br>

## Installation

### Requirements

- Home Assistant **2026.9.0** or newer
- The [schwoerer_lueftung](https://github.com/josa42/homeassistant-schwoerer-lueftung)
  integration, set up and reporting
- A Schwörer WGT. A WRT has nothing to heat with, so most of this does not apply.

<br><br>

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** and search for "Schwörer Climate Control"
3. Confirm the unit's entities. They are discovered, so this is normally a matter
   of pressing submit.
4. On the integration page, choose **Add a room** once per room. Each room gets
   its own device.

Shared settings live on the hub and every room inherits them. Any of them can be
overridden per room, and each decision records both the value it used and which
level it came from.

A room is a name, a thermostat, and whatever measures it. For a room of the unit
the thermostat is its own `climate` entity, whose hvac mode is the auxiliary
heater. For a room the unit does not heat it is any other `climate` entity: a
radiator valve, or a `generic_thermostat` in front of a relay. Hysteresis and
minimum run times belong to that thermostat, which in the case of a
`generic_thermostat` already solves them.

### The unit stays in manual

The controller sets the fan level, both releases and every setpoint itself. The
unit's own seasonal programme would work against that, so the operating mode has
to stay on manual. It is read and never written, and a repair is raised if it
reads anything else.

<br><br>

## How it decides

The mode says which direction of energy is allowed, and it is named after that
rather than after the season:

| Mode | What it allows |
| --- | --- |
| Heating | The heat pump may be released, the auxiliary heaters may run |
| Ventilation | Neither. The base function keeps running |
| Cooling | Cooling may be released, night air may be used |

Holiday is a modifier on top, not a fourth mode, because a holiday in January
still needs frost protection and reduced setpoints while one in July needs
neither.

Below the frost limit, heating happens whatever the mode says. That also holds
when the outdoor reading has gone missing, which is exactly when a freezing house
most needs it.

Air quality wins on the fan: humidity or CO₂ in any room raises the level, at
night too. The fan select caps or raises that with `quiet` and `boost`, and a
fixed stage overrides everything.

<br><br>

## Writing as little as possible

Nothing is written unless it differs from what the device reports. In a steady
state that means no Modbus traffic at all, and what is left are real transitions.
A bundle is paced rather than sent at once, and no bundle goes out within a minute
of the last one.

Comparing against the device rather than against a memory of what was sent has two
consequences worth knowing. A write that does not arrive is attempted again on the
next evaluation without anything extra being built. And one that never arrives is
counted, and raises a repair naming the register.

A value the device is not currently reporting is not a difference. After a restart
or a failed poll the current value is unknown, so nothing is written, which is
what stops every register being rewritten whenever Home Assistant starts.

**Dry run** decides and publishes everything and sends nothing. It is on for a
fresh install, so the decisions can be watched for a few days before anything
reaches the unit.

<br><br>

## Entities

| Device | Entities |
| --- | --- |
| Central | Active, holiday and dry run switches, mode and fan selects, decision sensor, degraded indicator, heat recovery sensor |
| Each room | Decision sensor |

**Active** off means no register is written at all. The unit keeps running on its
last values and the decision sensors keep showing what the controller would do,
which makes it the switch to reach for while working out why it did something.

The decision sensor carries the intent as its state, plus the sentence, the inputs
with their age, the conditions with their outcome and every setting with the level
it came from. Those last three are kept out of the recorder, because they change
shape on every evaluation.

<br><br>

## Answering "why was it on at three in the morning"

The sensors answer what is true now. The question is almost always about the past,
so every change also writes a logbook entry carrying the same sentence, per room
and for the unit. A setpoint drifting by a tenth is not a change and does not
appear.

The **diagnostics** download has the full trace, plus the writes the controller
would send right now and whether each is needed, which is the answer to "it
decided that, so why has nothing happened".

Three things raise a repair: the unit left manual mode, a configured input has
been unreadable for an hour, and a register will not take its value. An input that
misses a single poll is not a repair.

Notifications go to one notify service and gather for five minutes. A release
turning over is worth a message, because it is the expensive thing in the house
starting or stopping. A fan level is not.

<br><br>

## Dashboard

The integration ships a dashboard strategy that builds the whole dashboard from
the entity registry, so a room added later appears on its own.

Create a new dashboard, open its raw configuration editor and put in:

```yaml
strategy:
  type: custom:schwoerer-climate-control
```

You get an overview with the controls and the current decision, and a debug view
laying out the decision behind the unit and behind every room: the sentence, the
conditions with their outcome, the readings with whether they are reporting, and
every setting with the level it came from. To place just one of them inside a
dashboard you already have, use it as a view strategy instead:

```yaml
views:
  - strategy:
      type: custom:schwoerer-climate-control
      view: debug
```

It is built from Home Assistant's own cards, so it installs no custom card and
stays out of the way of
[schwoerer-lueftung-cards](https://github.com/josa42/homeassistant-schwoerer-lueftung-cards).

<br><br>

## The bypass

The bypass damper cannot be commanded. There is no write register for it on any
known firmware, and the unit's own controller drives it. What can be reached are
the conditions it decides from, and two of those the controller writes anyway: the
heating and cooling function has to read cooling for the damper to open at all,
and a room setpoint below the room temperature is the cooling demand it looks for.
Stage 0 shuts it, so cooling never asks for stage 0.

On the unit this was written for, the damper moves and the air does not. Supply air
shows full heat recovery whether the register reports open or closed, which is a
fault in the bypass path rather than in the actuator. Night cooling therefore
cools nothing there until that is found.

That is why the integration publishes the recovery it measures rather than
assuming the lever works. A bypass that starts working shows up at once, and one
that does not cannot be mistaken for a controller that is not trying. The
measurements are in
[docs/research/001-bypass-control.md](https://github.com/josa42/homeassistant-schwoerer-lueftung/blob/main/docs/research/001-bypass-control.md)
in the ventilation repository.

<br><br>

## Development

```bash
make install     # create venv and install test dependencies
make test        # run the test suite
make lint        # run ruff

make dev-up      # start Home Assistant at http://localhost:8123
make dev-restart # restart after code changes
make dev-down    # stop it again
```

`make dev-up` mounts `custom_components/` straight into the container, so the
integration is live in a throwaway Home Assistant without touching your real
instance.

The decision engine and the bypass measurement are pure functions with no Home
Assistant imports, so most of the behaviour is testable directly.

### Releasing

```bash
./scripts/release.sh 0.2.0
```

Runs the tests and the linter first, then bumps the manifest version, dates the
changelog, commits, tags and pushes. The release workflow builds the zip from the
tag. A failure before the push leaves the working tree untouched.

<br><br>

## License

MIT, see [LICENSE](LICENSE).

<br><br>

## Disclaimer

Unofficial, and not affiliated with or endorsed by Schwörer Haus KG.
