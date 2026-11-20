# Make the house part of the plan

ShabbatFlow is an **independent Home Assistant custom integration** for preparing Shabbat and Yom Tov schedules, observing real household device activity, and refining future plans. The current release provides planning and observation; it does **not execute lighting or HVAC schedules**. Official HA verification and HACS inclusion have not been established.

## Install the preview

1. Back up your Home Assistant configuration and any previous ShabbatFlow integration/storage.
2. Download the `shabbat-flow-preview` artifact from a successful [checks workflow](https://github.com/DovOps/ha-shabbat-flow/actions/workflows/checks.yml), or build the package from the repository with `python3 scripts/build_ha.py --check --zip`.
3. Extract the versioned ZIP into your HA configuration directory, creating `custom_components/shabbat_flow/manifest.json` without an extra nested folder.
4. Restart Home Assistant, then add **ShabbatFlow Preview** through Settings → Devices & services → Add integration.
5. Open the ShabbatFlow sidebar as an HA administrator. Review **Settings** for detected capabilities. Updates currently require a restart when the integration's Python code changes.

Compatibility is tested against HA 2026.8.2 and 2026.11.2. This is a custom preview, not a production scheduling release. It does not modify existing automations.

## Connect the house you already have

Choose HA areas, then work through the room wizard. Identify bedrooms, bathrooms, common areas and hallways; bind main lights, background lights and HVAC. Link shared bathrooms explicitly. HA labels can narrow device choices. Assigning an area or label in HA makes configuration easier, but never silently authorizes a device action.

Configure the built-in **Jewish Calendar** integration for your location, timezone, Israel/diaspora observance and candle/Havdalah settings. Enable its daily and yearly event calendars. ShabbatFlow reads future candles, sunrise and observance-end data; incomplete calendar data requires correction or deliberate manual entry.

## Prepare a particular weekend or holiday

Choose which rooms will be used, sleeping patterns, meals at home and afternoon hosting. Review the full one-, two- or three-day period. Adjust candle-relative lighting and separate HVAC timings, night/background changeovers, daylight breaks and morning use. Inspect existing automation forecasts as **unmanaged**, not as guaranteed or controlled events.

Export the plan as JSON or use PDF / Print. Review each schedule before relying on it; a preview does not activate any devices.

## Observe and learn

Start a plan observation to compare expected and observed activity, or a separate 1–48-hour climate study. Select HVAC zones, optional reference/weather sources, and associated lights or switches. Devices already On are captured at the start; no toggle is required. State sampling is approximately once per minute, with hourly thermal samples. Unknown intervals remain unknown, and device activity is evidence—not proof of occupancy.

Reports rank zones by sampled active minutes and combine thermostat readings, setpoints, modes, outdoor/reference temperature and activity bands. Download JSON or print the report to PDF. No automatic thermostat calibration is applied.

## Optional reminders and notifications

Settings detects available Twilio SMS UI and Companion App push actions. Both channels are off by default. Select a sender/recipient or app device, enable the desired channel and save. Lifecycle notifications can announce study start, early stop and completion. Report links require an HA administrator login; no public report file is created.

Pre-candle plan reminders are separately enabled app pushes. Configure multiple offsets before candles (defaults: 180, 60, 30 minutes). They send only on the local candle-lighting date while the same-provider issur melacha signal is explicitly Off. Missing data, active issur and excessively late reminders suppress sending. Reminders prompt review; they never activate a plan.
