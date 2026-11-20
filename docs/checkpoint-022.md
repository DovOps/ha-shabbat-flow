# Checkpoint 022 — setup shortcuts and current activity

## Changes
- Explicit room use, nap and family/hosting meal choices mark their simple day-level availability Home. Do not mark Away when removing a selection; preserve custom partial-day windows for explicit review. Other days remain unchanged.
- Green planner action at top and bottom shares validation, busy/error handling and navigation. Compact icon/name/status room links use the same validation as detailed feedback.
- Home-page overview separates browser-local saved drafts from HA-persisted scheduled/observing plan runs and climate studies. Concurrent kinds remain visible. Show local dates, individual report links, terminal latest-run and clear empty/unavailable states. Browser drafts can be explicitly reopened without creating a replacement. Routine unchanged polling preserves focused links.
- English/Hebrew requirements and guide updates; no new dependency, device command, notification enablement, automatic save or study start.

## Verification
- 77 Python core tests, 58 JavaScript tests, 112 HA compatibility tests each on 2026.11.2 and 2026.8.2 passed.
- Added explicit-use/multi-day/partial-day/removal tests, concurrent/terminal/scheduled run classification, browser storage and API failure tests, stable unchanged rendering and per-run report links. Extended shared-button busy-state test.
- Local Chrome fictional fixture: top planner error points to calendar issue; room shortcut opens its editor; compact status overview and empty states reviewed in English/Hebrew. Standalone icons use decorative fallback; live HA icon rendering for these new shortcuts remains an installed check.
- Package 0.16.4, generated-file/repository checks and both website locale production builds passed. Browser proofs kept outside reusable source.

## Rollout
Packaged, not installed. HA remains 0.16.3. Real saved-plan reopening and real concurrent-run presentation remain installation validation items. No production restart or device-control activation.
