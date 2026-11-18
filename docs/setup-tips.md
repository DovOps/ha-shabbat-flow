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
