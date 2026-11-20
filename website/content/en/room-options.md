# Room options explained

A preset fills several lighting settings at once as soon as you select it. It replaces the related phase settings below, not your device selections or HVAC settings. The selector returns to Current / custom settings so you can fine-tune them. Save & next commits the room; no device is controlled.

## Area type

### Bedroom

Bedroom: sleeping profiles control bedtimes and HVAC; extra night/morning phases are optional. Select actual overnight use in the dated plan.

### Common Area

Common area: combine meal lighting/HVAC, night changeover and an optional daylight break. No sleeping purpose or bathroom link is required.

### Bathroom

Bathroom: demand comes from linked rooms or anyone-home use. Its own daylight and optional night-light policy controls changeovers.

### Hallway

Hallway: configure circulation lighting with a night changeover, optional morning window or always-on access light. Review the preset before saving.

### Legacy shared/service area — choose its type

An older shared/service area needs an explicit type. Choose Bathroom, Common Area or Hallway after reviewing its existing settings.


## Apply a starting preset

### Current / custom settings

Keep the current settings. Choose another preset only to replace the phase defaults.

### No night or morning phase

Disables the added night and morning phases and evening main-light phase. Existing room-use and meal bindings remain.

### Evening → background lighting

Starts background lights after recreation or the evening meal ends; ends one hour before sunrise. Requires recreation use or an evening meal binding.

### Kitchen: main → night → morning main

While home: main lights before the changeover, night lights from candles +6 hours until sunrise +2 hours, then morning main lights. Review the main-off option and overlaps.

### Hallway night lighting

Night lights from candle lighting until one hour before sunrise; main lights off at the night transition. Does not enable meals or HVAC.

### Always-on access lights

Keeps main lights on whenever the plan says someone is home. No night/morning swap—useful for an entrance or an always-needed light.

### Hallway Day / Night / Off

Main lights before entertaining ends, then night lights until sunrise −1 hour. Morning main lights run from sunrise +2 to +4 hours.

## When should night lights run?

These phases are available for bedrooms too. Sleeping profiles also schedule bedroom lights: review overlapping demands in Preview. For an ordinary bedroom, keep these extra phases off unless you intentionally want night/background or morning lighting.

### Follow existing room-use lighting

Adds no separate night-light window. The room-use profile and other enabled phases still apply. This does not mean turn every light off.

### After recreation use ends, until morning

Starts after this room’s recreation window or evening meal finishes. Set the end relative to the next sunrise. Use this when background lighting should follow activity in this room.

### Evening-to-morning while home

Starts at your offset after candle lighting, regardless of meal end, only during planned home availability. Ends at the sunrise offset unless an existing automation owns the shutoff.

### At end of entertaining, while home

Uses the plan’s derived end of entertaining rather than a fixed candle offset. Night lights run only while home; main lights switch off at that transition.

## Who turns night lights off in the morning?

### Planner — use sunrise offset

The plan includes a night-light off event at the configured sunrise offset.

### Existing HA automation — schedule On only

The plan turns night lights on but leaves their morning shutoff to your existing automation. Check that automation separately; this does not create or enable it.

## Daytime lighting

### Always on while needed

Keep the light needed throughout its demand window. This is not necessarily the entire observance: room links and home availability determine demand.

### Daylight break

Add a daylight break: off after sunrise and back on before sunset, only within the existing demand window. Review the two offsets.

## How should this HVAC be scheduled?

### Do not schedule this HVAC

No HVAC events are generated for this room, even when a unit is selected.

### Schedule On/Off only — preserve settings

Schedule on/off only. Keep the unit’s heat/cool mode and target temperature. Future execution requires a verified resume-capable adapter.

### Use a specific heating/cooling profile

Choose the heat/cool mode, target temperature and fan settings explicitly, or copy usable current settings.

## When are its lights needed?

### During this room’s use window

This bathroom is needed only while this linked room is in use; other linked rooms can extend the combined window.

### Throughout Shabbat / the continuous holiday when this room is used

If this linked room is used, request bathroom lighting for the whole observance, subject to its daylight/night policy.

## Nap and late wake-up defaults

Clock times use the local date of that day’s sunrise. A nap must end after it starts and within that day. End of day means that selected segment, not the end of a multi-day holiday. Review the resolved dated times in the plan. Existing defaults remain unchanged until saved.

Choose **After sunrise** or **Local time of day** for nap start and late wake-up. For example, 14:00 is a fixed afternoon nap; 07:00 after sunrise moves with the seasons. Nap end can use a duration, a clock time, or the selected observance-day boundary. Defaults are applied when adding a new nap; existing dated naps do not change. The dated plan also offers an explicit end-of-day button and editable start/end times.

Offsets use **HH:MM**: `06:00` after candles is six hours later; `-01:00` relative to sunrise is one hour earlier. `00:30` is thirty minutes. Clock-time fields use the local time zone. Review the full schedule for overlaps; independent meal or room demands can keep a light on.

Icons use HA area/entity assignments when available. Standalone examples use decorative fallback symbols; labels are never replaced by icons.
