# Checkpoint 018 — explainable setup, rest timing and localized gallery

## Delivered locally
- Six workflow screenshots per language: room setup, daily planning, timeline, event list, climate report and plan comparison. Fictional fixtures only; source and refresh instructions are recorded in the gallery README.
- EN/HE room-option guide, offline help and selected-option explanations for area type, every preset, night timing, release ownership, daylight, HVAC and bathroom linkage. Bedroom applicability and overlapping lighting demand are explicit.
- Read-only HA area/entity icon metadata with registry-override precedence. Setup room/device lists, planner room tiles/event rows and climate-study selection use existing HA frontend rendering when available. Standalone fallback and labels remain; native dropdown options remain text-only. Icon metadata is excluded from structural revision and compiler input.
- Additive bedroom rest defaults: sunrise offset or local clock time for nap start/wake; duration, clock time or selected-day end for nap end. Existing defaults retain their meaning. New dated naps resolve timezone-aware timestamps; existing dated naps remain unchanged. Explicit dated end-of-day shortcut.
- HH:MM lighting/rest offset inputs retain integer-minute contracts; local clock fields are separate. Invalid offsets are flagged and blocked from save/preview.

## Verification
- Python core: 76 passed. JavaScript: 51 passed, including clock defaults, signed HH:MM parsing, invalid ranges and DST gap/fold rejection.
- HA integration: 109 passed on 2026.11.2 and 109 on 2026.8.2, including clock-default persistence and icon precedence/revision/compiler invariance.
- Local browser review: English/Hebrew screenshot pairs and Hebrew brochure; clock nap/wake and day-end controls; dynamic night help; invalid offset marking and correction; translated help.
- Both website locales build; 132 pages checked with project-relative assets, guide and canonical specification coverage.

## Boundaries
0.16.0 is packaged, not installed in HA. HA remains on 0.15.0. Native HA icon rendering has not been live-validated; standalone fallback has. No device commands, registry changes, notification sends or HA restart occurred. Website deployment remains gated by owner enablement.
