# Manual installation

The [button in the README](../README.md#installation) does all of this in one
click. These steps are for when that button does not work, or when you would
rather not use HACS at all.

## Adding the repository to HACS by hand

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Open HACS → Integrations
3. Click the three dots menu (top right) → Custom repositories
4. Add repository URL: `https://github.com/josa42/homeassistant-schwoerer-climate-control`
5. Category: Integration
6. Click "Add"
7. Click "Download" on the Schwörer Climate Control card
8. Restart Home Assistant

## Without HACS

1. Download the latest release from [GitHub releases](https://github.com/josa42/homeassistant-schwoerer-climate-control/releases)
2. Extract the `custom_components/schwoerer_climate_control` folder
3. Copy it to your Home Assistant `custom_components` directory:
   ```
   config/
   └── custom_components/
       └── schwoerer_climate_control/
   ```
4. Restart Home Assistant

Updating means repeating this with the new release and restarting again. HACS
does it in one click instead, which is why it is the recommended route.
