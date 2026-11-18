# Tips for easier household setup

Labels are optional. ShabbatFlow uses your chosen labels to narrow setup choices; they do not authorize devices or change schedules automatically. Configure labels in Home Assistant, then choose their meanings in ShabbatFlow's **Use HA labels to simplify setup** section. Any names and languages are supported.

| Suggested label | Apply in HA to | Used for |
| --- | --- | --- |
| Bathroom | Individual light/switch entities, or devices whose relevant light/switch entities are all bathroom lights | Bathroom area choices and main-light choices in shared/service areas |
| Room Main Lights | Individual light/switch entities, or their devices | Main-light choices |
| Background/Night Lights | Individual light/switch entities, or their devices | Night/background-light choices |
| Bedroom | Areas | Room-list filter and explicit Sleeping suggestion |
| Common Area | Areas | Room-list filter and explicit Recreation suggestion |

1. Assign devices/entities to the correct HA areas first. An entity's explicit area takes precedence over its device's area.
2. Prefer entity labels on multi-channel devices when only some switches belong to a role. A device label includes all its eligible light/switch entities in the chooser; sensors and HVAC are not added to lighting lists. Area labels do not label all contained lights.
3. Map the labels in ShabbatFlow and save progress. You can skip any mapping. Labels never need an exact reserved name.
4. Choose rooms, optionally filtering by Bedroom or Common Area. Both labels can apply to an area; Apply suggested room uses adds the corresponding purposes only when clicked. Weekly use remains a separate decision.
5. Review main/night lights and bathroom links. Bathroom choices are areas containing matching entities; a label does not say which bedroom uses that bathroom. Configure shared lights once, then link the relevant rooms explicitly.
6. Use **Show all devices for this room** to ignore labels. **Show devices from all areas** additionally removes area scoping; it does not itself remove label filtering. Use both for any eligible device, including unassigned devices. **Show all bathroom areas** bypasses the bathroom-area filter. Existing selections always remain visible.
7. HA label changes appear through inventory refresh. Renaming keeps the mapping; deleting a mapped label displays a warning. Select another label or clear that mapping. No selected device is silently removed and no new one is selected. When editing during a structural change, refresh and review before saving.
8. Save room setup and create a new dated planner workspace to use changed device mappings. Existing workspaces are snapshots. This preview never controls devices or edits HA labels.

If no labels match, use the Show all controls or check entity/device labels and area assignments in HA. Disabled entities remain unavailable for new selection. A switch label is only a selection aid: review whether the switch actually controls the intended light.

See [Home Assistant labels](https://www.home-assistant.io/docs/organizing/labels/) and [areas](https://www.home-assistant.io/docs/organizing/areas/).
