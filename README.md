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
> Under construction. Nothing is released yet, and the integration does not do
> anything useful at this point. The decisions it is being built from, and the
> reasoning behind them, are written down in [docs/design.md](docs/design.md).

<br><br>

## What it will do

Every evaluation produces one decision per room plus one for the system, and each
decision carries the inputs it read (with their age), the conditions it applied,
the settings it used and where each of those came from. Changes are written to the
logbook as finished sentences, so the answer to "why was the auxiliary heater on
at three in the morning" survives a restart.

Three operating modes say which direction of energy is allowed: heating,
ventilation only, or cooling. Holiday is a modifier on top of that rather than a
fourth mode, because a holiday in January still needs frost protection and one in
July does not.

<br><br>

## Requirements

- Home Assistant **2026.9.0** or newer
- The [schwoerer_lueftung](https://github.com/josa42/homeassistant-schwoerer-lueftung)
  integration, set up and reporting
- A Schwörer WGT. A WRT has nothing to heat with, so most of this does not apply.

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

The decision engine is a pure function with no Home Assistant imports, so most of
the behaviour is testable directly.

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
