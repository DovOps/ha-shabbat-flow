# Implementation plan

1. Extend stored household intent with versioned selected/draft/ready status, explicit bathroom links/policies and resumable progress. Define migration from schema 1, preserving old use-window semantics. Separate incomplete draft validation from ready configuration validation.
2. Extend sanitized inventory with observed current HVAC settings; exclude telemetry from structural digests. Continue validating stored profiles against capabilities.
3. Add deterministic bathroom demand generation: room-window, full continuous period and explicit home intervals. Use existing physical-load demand union and test cross-day boundaries. Unfinished rooms and unresolved dependencies cannot leak actions.
4. Replace the all-area form with selection, one-room steps and summary. Persist Save & next; leave failed saves on the current step. Reuse bathroom setup. Keep calendar and dated-plan controls separate. Add localized supported-value HVAC controls.
5. Add EN/HE, keyboard/mobile coverage and targeted persistence/concurrency/compiler tests. Preserve automatic calendar and advanced override regression checks.
6. Run required checks and HA compatibility tests. Package a new version, back up installed code and own settings, refresh the authorized installed preview, and verify without device calls or fabricated production mappings.
7. Commit with sign-off, push the authorized branch and merge the tested checkpoint to main. Record actual evidence and any remaining limitations.

No runtime dependency change is proposed. Feature 007's HA registries/Store and 008's Jewish Calendar interface remain the dependency set.

## Schedule badge follow-up
Map each preview action to a semantic badge type, apply distinct On/Off treatments and localized labels, then test mixed binary/HVAC events and desktop/mobile EN/HE rendering against US5. Implemented and installed in 0.5.1; see verification.md.

## Power-only HVAC follow-up
Add a dedicated `hvac_power` load/action contract with exact on/off-only keys, separate from setting-bearing HVAC profiles. Reuse independent lead/end windows and shared-demand conflict handling. Keep existing `none` settings unscheduled. Expose native power feature flags as diagnostics, not restoration guarantees; HA's base climate turn-on fallback can choose a mode. No execution adapter is part of this change. Implement semantic preview badges without modifying events or schedule digest. Label-guided filtering is now approved in the follow-up below.

## Label-guided setup follow-up
Read HA's built-in label registry and direct membership arrays. Add optional `label_filters` to schema 2 with empty defaults; old request shapes preserve stored mappings. Keep filtering in a pure frontend model, separate from schedule compilation. Add editable label setup ahead of room selection, explicit area-purpose suggestions, role-specific candidate filters and independent area/label escape controls. Supply EN/HE help and a repository Tips page. Verify both HA versions and fictional browser fixtures; package the next preview version.

## Bathroom lighting policy
Add optional bathroom lighting intent under room setup, preserving legacy defaults. Read optional dated sunset from the existing daily calendar. Resolve deterministic allowed intervals for each light set in the workspace snapshot, intersect demand intervals in the compiler before union, and carry localized fallback warnings into preview. Offer independent daylight and night toggles/offsets with EN/HE controls. Test calendar, policy, compiler and HA persistence before packaging; no device executor.

## Full room changeovers and end behavior
Use optional validated room phase settings and generated home-driven windows for kitchen/hallway/morning main lighting. Recreation-end background uses its own interval after the main-light interval. Generate separate evening/daytime meal groups; evening meals can begin background demand at meal end, lunch never does. Use the same HVAC intent/lead contract for meal HVAC. Keep final-boundary release behavior as explicit configuration (`post_shutoff`), default false in new household workspaces and preserved in legacy explicit exports. Generic old configurations without the new key retain their prior compiler behavior. Preview summaries display meal-linked rooms and fallback notices.

## Explicit completion feedback
Share pure room validation between proactive status rendering and completion. Render persistent feedback at the room heading and save controls without replacing focused form fields during polling. Keep remote save errors separate from local draft validation. No new dependencies or changes to scheduling semantics.

## Common areas and composable daylight policy
Add optional explicit area_type to schema-2 setup; absent values retain legacy behavior. Separate area classification from purposes and reusable lighting policy. General phases own night transitions when enabled; daylight masks clip lighting rules across home/meal/recreation demands, never HVAC or one-shot sleeping Off rules. Keep backend compatibility and require explicit user conversion of legacy common/service areas. No new dependencies.

## Bedroom rest follow-up — implementation
Implement US12 as explicit dated overnight wake-up overrides and separately identified nap windows. Preserve existing overnight profiles and their lighting behavior; do not model a nap by blindly cloning the overnight sleeping group. Compile nap windows into HVAC-only demand plus explicitly opted-in bathroom demand, using existing physical-load conflict/union handling and independent preconditioning. Keep displayed room-use duration separate from lighting triggers where a wake-up override extends HVAC.

Persist reusable rest defaults in household setup and actual selections in the dated workspace. Define and version the additive schema before implementation, with old inputs meaning no naps and unchanged wake-up behavior. Reuse supplied local timezone/calendar coverage and the existing local date/time ambiguity handling. Extend reasons and summaries so the existing HVAC chart and PDF can explain nap versus overnight demand. Update compiler contracts and migration tests together; no new calendar or execution dependency is approved.

Implementation contract for US12: use optional top-level `plan.naps` records (id, room, sleeping profile, segment, start/end, lead_minutes and bathroom_targets) and optional `hvac_end` on planner-controlled sleeping room uses. Preserve existing input semantics when absent. Nap rule expansion selects HVAC actions and optional shared-light targets only and uses the explicit nap window. Planner sleeping/nap overlaps are resolved by physical demand union; existing-control overlap remains a blocker. Wake overrides affect HVAC release only. Reusable nap defaults live on a sleeping profile's optional `rest_defaults`; per-room/day edits never change them implicitly. Afternoon hosting is an optional `afternoon` meal/activity record with existing meal groups; old workspaces add it only by explicit user action.

US13 implementation: extend optional phase settings with constant_main, morning_end, night_release and independent evening/daytime HVAC plus recreation_hvac booleans. Missing meal HVAC flags inherit the old combined binding. Add entertaining_end as a derived compiler anchor using selected evening uses/meals, falling back to candles +360; dynamic home rules intersect availability. Existing-automation release uses a point On and a localized warning, not a fabricated Off or automation overlay. Keep examples fictional and leave deployment separate.

0.15.1 presentation: update display labels while preserving technical IDs and custom entry titles; shared CSS navigation and dependency-state classes reuse existing discovery codes and catalogs. Verify packaging, lifecycle title tests, frontend checks and EN/HE visual presentation before a separately authorized HA update.

Add localized inline selection descriptions and a linked guide. Keep icon metadata separate from schedule configuration; render via the same-origin HA frontend with safe fallback. Extend rest defaults additively, resolving local clock choices against the segment sunrise date with existing DST validation. Format offset input as HH:MM while preserving minute contracts. Validate old fixtures and both HA versions before packaging.

0.16.2: Group icons with text instead of a third flex child. Cache HA-owned native SVG rendering and copy the graphical result into the iframe; extend timeline labels. Test cache ownership, cleanup and standalone fallback; live HA rendering verification remains required.

0.16.3: Place checkbox first in DOM for climate rows and at logical start through shared flex ordering elsewhere. Keep icon/name adjacent and isolate mixed-direction names.

0.16.4: Reuse the planner validation/navigation handler for both green shortcuts. Derive compact room-status links from shared room feedback. Add a pure activity-summary model and read the existing observer listing; distinguish browser-local saved draft from persisted observer runs, show timestamps/status/report links and explicit unavailable states. Resume browser drafts only on an explicit link. No new runtime dependency or device calls.
