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
