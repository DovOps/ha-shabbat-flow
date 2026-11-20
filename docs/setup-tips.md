# Tips for easier household setup

Labels are optional. ShabbatFlow uses your chosen labels to narrow setup choices; they do not authorize devices or change schedules automatically. Configure labels in Home Assistant, then choose their meanings in ShabbatFlow's **Use HA labels to simplify setup** section. Any names and languages are supported.

| Suggested label | Apply in HA to | Used for |
| --- | --- | --- |
| Bathroom | Individual light/switch entities, or devices whose relevant light/switch entities are all bathroom lights | Bathroom area choices and main-light choices in bathrooms |
| Room Main Lights | Individual light/switch entities, or their devices | Main-light choices |
| Background/Night Lights | Individual light/switch entities, or their devices | Night/background-light choices |
| Bedroom | Areas | Bedroom type and Sleeping suggestions |
| Common Area | Areas | Common Area type suggestion (no automatic recreation purpose) |
| Bathroom Area | Areas | Bathroom type suggestion |
| Hallway | Areas | Hallway type suggestion |

1. Assign devices/entities to the correct HA areas first. An entity's explicit area takes precedence over its device's area.
2. Prefer entity labels on multi-channel devices when only some switches belong to a role. A device label includes all its eligible light/switch entities in the chooser; sensors and HVAC are not added to lighting lists. Area labels do not label all contained lights.
3. Map the labels in ShabbatFlow and save progress. You can skip any mapping. Labels never need an exact reserved name.
4. Choose rooms, optionally filtering by Bedroom or Common Area. Map area-type labels separately from entity-light labels. Unique matches default newly selected empty areas; existing configured rooms need Apply suggested area type. Conflicting labels require a choice. Explicit types stay fixed when labels change. Weekly use remains a separate decision.
5. Review main/night lights and bathroom links. Bathroom choices are areas containing matching entities; a label does not say which bedroom uses that bathroom. Configure shared lights once, then link the relevant rooms explicitly.
6. Use **Show all devices for this room** to ignore labels. **Show devices from all areas** additionally removes area scoping; it does not itself remove label filtering. Use both for any eligible device, including unassigned devices. **Show all bathroom areas** bypasses the bathroom-area filter. Existing selections always remain visible.
7. HA label changes appear through inventory refresh. Renaming keeps the mapping; deleting a mapped label displays a warning. Select another label or clear that mapping. No selected device is silently removed and no new one is selected. When editing during a structural change, refresh and review before saving.
8. Save room setup and create a new dated planner workspace to use changed device mappings. Existing workspaces are snapshots. This preview never controls devices or edits HA labels.

If no labels match, use the Show all controls or check entity/device labels and area assignments in HA. Disabled entities remain unavailable for new selection. A switch label is only a selection aid: review whether the switch actually controls the intended light.

See [Home Assistant labels](https://www.home-assistant.io/docs/organizing/labels/) and [areas](https://www.home-assistant.io/docs/organizing/areas/).

## Complete lighting changes
- Keep main and night/background lights in distinct roles. For a kitchen, main can be spots and night can be island lights. For a dining area, night can be background lights. Presets never infer these devices from names.
- Use the background preset for the end of recreation use; use kitchen or hallway presets for home-driven evening/morning behavior. Review offsets each season. Meal options link selected rooms' main lights and HVAC to Family/Hosting meals.
- Bathrooms with natural light may use Daylight break; others should retain Always on. Independently enable bathroom night switching only when both main and night lights are mapped. These settings repeat each dated day of the supplied holiday.
- Post-observance shutoff is unchecked by default. The preview ends without issuing a final off command. Existing automations are unaffected; inspect potential overlap before any future execution.
- Save setup, then create a new dated workspace. Older exports retain their original group rules, meal targets and end behavior.

## Area types and combined profiles
Choose Bedroom, Common Area, Bathroom or Hallway based on use, regardless of the HA name. Common areas can combine meal lighting/HVAC, home night/morning phases and a daylight break without a sleeping purpose or bathroom link. Hallways expose a selectable night preset; classification does not automatically enable it.

Daylight breaks suppress selected main/night lighting, including meals, but leave HVAC running according to its own demand. Missing sunset retains lights with a warning. Converting a legacy service area to Common Area preserves device choices, meals and daylight settings, keeps existing general phases (or converts legacy bathroom night timing when none exist), and disables the conflicting bathroom night policy. Save and create a new workspace to preview the change.

## Naps, late wake-up and afternoon hosting
In the dated planner, expand a selected bedroom's wake-up controls to keep its HVAC running later without delaying bedroom-light shutoff. The default leaves the existing profile unchanged; Late uses the room's sunrise-relative default, and Custom accepts a local date/time.

Add a nap separately for any configured bedroom, including a room unused overnight. Review its start/end and HVAC lead time. A nap normally adds only HVAC; shared bathroom lights are optional and retain their configured daylight/night policy. A room without planner HVAC shows an explanation and will not acquire HVAC commands. Reusable defaults are in bedroom setup; changing them does not rewrite existing dated workspaces.

On Shabbat, add Afternoon hosting / Seudah Shlishit if needed and choose Hosting. Review the lunch-linked groups and local time window. The final Shabbat segment defaults to end minus 2.5 hours through end; an internal Shabbat-to-holiday boundary requires explicit times. Existing daylight breaks can suppress light demand. Compatible concurrent demands keep a device on until all have ended. The post-observance shutoff option still controls final releases.

## Always-on access and circulation phases (0.11.0)
Choose only the circuits you actually want in each area's Main lights / Night lights. Use Always-on access lights for entrance or convenience lighting that should remain on while home. Use Hallway for nightlights at candles and explicit main-light Off; use Hallway Day / Night / Off for an entertaining-end changeover and a bounded morning main-light interval. An entry shelf light can use the Night lights role in its own hallway area; dining backgrounds can follow after-use or the shared end-of-entertaining anchor. Role labels can help find these circuits without special hard-coded names.

Existing morning automation ownership emits On only each night, with a warning that the chart does not forecast the external Off. Review that timer separately. The planner neither disables it nor pretends it has imported its schedule. Always-on circuits must not also be targets of an external shutoff if you intend uninterrupted availability.

Lighting and HVAC now have separate dinner/lunch checkboxes. Enable daytime HVAC in every participating common area, set HVAC intent above, and independently decide whether recreation use and dinner need HVAC. Continuous historical On is not a default to copy. Save and open a fresh dated plan to capture updated bindings; old exports stay unchanged.

## Settings, dependency checks and study notifications
Open **Settings** from house setup or the observation controls. Refresh after configuring HA integrations. Cards distinguish required capabilities, requirements specific to room/climate features, preferred Jewish Calendar with manual fallback, and optional features. Detection is not delivery or future-calendar-coverage validation.

For notifications, select **App push** (recommended if you use the HA Companion App), **SMS**, or both. Select the registered app device and/or Twilio sender plus an E.164 recipient, choose study types/events/language, enable the desired channels, then save. Saving sends nothing. Only subsequent study transitions qualify. An already-running study can notify on its future completion; enabling does not retroactively announce its start.

Completion/stop links open the retained study report with PDF / Print and JSON export. HA administrator authentication is required; no report is made public. App push uses the app's HA connection; SMS links require a configured HTTPS external URL. Remote connectivity, phone permissions, SMS costs/provider restrictions and delivery must be verified separately. A submitted/unconfirmed status is not proof of handset delivery. There is no automatic retry after an uncertain attempt, and disabling cannot recall a notification already in flight.

Pre-candle reminders are an independent app-push option in Settings. Default offsets are 180, 60 and 30 minutes before candle lighting; edit the comma-separated minutes as needed. They require Jewish Calendar event calendars and its unique enabled issur status sensor. Reminders send only on the same local date as the first candle of the upcoming continuous period, while issur is explicitly off. Unknown/on status, calendar gaps and reminders over two minutes late suppress delivery. A draft does not silence reminders: these are review prompts, never plan activation.

## Main-page shortcuts and current activity
The green **Open planner with my rooms** button is available at both the top and bottom of house setup. Both require the same saved, valid setup and calendar coverage. **Rooms at a glance** links directly to each room editor, with Ready, Draft or Needs attention statuses.

**Plans and studies** separates a draft saved in this browser from a plan observation or climate study persisted in HA. An observation can run even if this browser has no draft. The tiles show scheduled/observing status, dates and report links; completed/stopped runs are shown as the latest run, not as active. Failed discovery is shown as unavailable. Nothing here activates device control.

In the dated planner, selecting a used room, a nap or a family/hosting meal sets the simple day-level **Someone home** choice. Removing that use does not automatically mark everyone away. If you entered custom partial-day home/away windows, these remain unchanged: review them in Advanced settings for conflicts.
