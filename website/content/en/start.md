# Make the house part of the plan

Shabbat Flow is an **independent Home Assistant custom integration** for preparing Shabbat and Yom Tov schedules, observing real household device activity, and refining future plans. The release provides planning, observation and a separately armed lighting pilot. HVAC execution remains unavailable. Official HA verification and HACS inclusion have not been established.

## Install the preview

1. Back up your Home Assistant configuration and any previous Shabbat Flow integration/storage.
2. Download the `shabbat-flow-preview` artifact from a successful [checks workflow](https://github.com/DovOps/ha-shabbat-flow/actions/workflows/checks.yml), or build the package from the repository with `python3 scripts/build_ha.py --check --zip`.
3. Extract the versioned ZIP into your HA configuration directory, creating `custom_components/shabbat_flow/manifest.json` without an extra nested folder.
4. Restart Home Assistant, then add **Shabbat Flow** through Settings → Devices & services → Add integration.
5. Open the Shabbat Flow sidebar as an HA administrator. Review **Settings** for detected capabilities. Updates currently require a restart when the integration's Python code changes.

Compatibility is tested against HA 2026.8.2 and 2026.11.2. This is a custom preview, not a production scheduling release. It does not modify existing automations.

## Connect the house you already have

Choose HA areas, then work through the room wizard. Identify bedrooms, bathrooms, common areas and hallways; bind main lights, background lights and HVAC. Link shared bathrooms explicitly. HA labels can narrow device choices. Assigning an area or label in HA makes configuration easier, but never silently authorizes a device action.

Configure the built-in **Jewish Calendar** integration for your location, timezone, Israel/diaspora observance and candle/Havdalah settings. Enable its daily and yearly event calendars. Shabbat Flow reads future candles, sunrise and observance-end data; incomplete calendar data requires correction or deliberate manual entry.

## Prepare a particular weekend or holiday

Choose which rooms will be used, sleeping patterns, meals at home and afternoon hosting. Review the full one-, two- or three-day period. Adjust candle-relative lighting and separate HVAC timings, night/background changeovers, daylight breaks and morning use. Inspect existing automation forecasts as **unmanaged**, not as guaranteed or controlled events.

Export the plan as JSON or use PDF / Print. Review each schedule before relying on it; a preview does not activate any devices.

## Observe and learn

Start a plan observation to compare expected and observed activity, or a separate 1–48-hour climate study. Select HVAC zones, optional reference/weather sources, and associated lights or switches. Devices already On are captured at the start; no toggle is required. State sampling is approximately once per minute, with hourly thermal samples. Unknown intervals remain unknown, and device activity is evidence—not proof of occupancy.

Reports rank zones by sampled active minutes and combine thermostat readings, setpoints, modes, outdoor/reference temperature and activity bands. Download JSON or print the report to PDF. No automatic thermostat calibration is applied.

## Optional reminders and notifications

Settings detects available Twilio SMS UI and Companion App push actions. Both channels are off by default. Select a sender/recipient or app device, enable the desired channel and save. Lifecycle notifications can announce study start, early stop and completion. Report links require an HA administrator login; no public report file is created.

Pre-candle plan reminders are separately enabled app pushes. Configure multiple offsets before candles (defaults: 180, 60, 30 minutes). They send only on the local candle-lighting date while the same-provider issur melacha signal is explicitly Off. Missing data, active issur and excessively late reminders suppress sending. Reminders prompt review; they never activate a plan.

[Room options explained](./room-options.md)

### Home-page overview
Use the green **Open planner with my rooms** button at the top or bottom of house setup. **Rooms at a glance** links to room editors and shows Ready, Draft or Needs attention.

**Plans and studies** shows the saved plan in this browser separately from scheduled/active plan observations and climate studies in HA. A saved draft is not activated device control. Report links open the corresponding run; empty states and unavailable status are distinct.

Selecting rooms in use, naps or meals at home sets the simple day-level **Someone home** choice automatically. Custom partial-day availability is preserved for review. Removing a selection does not automatically mark everyone away.

## Optional lighting control pilot
After preview, open **Schedule and observe**. Review the exact dates and device subset, record weekday On/Off verification, approve, then schedule explicitly. Only reviewed lighting controls can run; HVAC, fans and appliances remain excluded. Existing automation conflicts block control. Devices already in the required state receive no command. Save and Preview do not activate anything. Nobody home automatically makes meals Away; all-away plans cannot arm. Check the execution status and linked report afterwards. This is a limited pilot requiring device qualification, not full-house live validation.

## Test the actual plan on a weekday

In 0.21.0, preview your saved weekend plan and choose **Rehearse this exact plan**. Select an actual scenario/time and areas. **Run this transition only** uses actions at that moment; **Set up this moment** uses the latest known planned state. Simulate first, inspect the targets and exclusions, then explicitly apply eligible lighting changes while present to supervise. Shared bathrooms need separate selection. Tests never arm the weekend schedule.

Refresh results, record feedback and export the plan plus rehearsal JSON. **Review restore** offers only confirmed changes that have not been changed externally afterward. No automatic restore or restart replay. Real tests require an inactive Jewish Calendar observance signal; HVAC, fans and appliances remain simulation-only. Installation and owner hardware acceptance are separate rollout steps.

## HVAC/fan rehearsal and short-day naps (0.22.0)
Immediate rehearsals include HVAC power and mapped room fans. If a unit is Off with no known mode/speed, turn it on in HA with your preferred settings and use **Capture current settings (no device changes)**. Review again before applying. No climate temperature or fan-mode commands are sent; device-side setting resets are reported as failures. Fans need explicit activity windows. Weekend scheduled control remains lighting-only.

New duration-based naps are shortened visibly at the day's end when needed. Invalid clock choices show feedback next to Add nap. Room defaults and existing naps are preserved.

## Practice before your first rollout

Follow the [adoption playbook](adoption.md): map the house, preview, observe, rehearse on a weekday, restore, and approve a small tested lighting subset. It explains what each action changes and what still needs qualification. In HA, open **Guide** in the top navigation or the rehearsal help link; help opens separately so your draft remains open.
