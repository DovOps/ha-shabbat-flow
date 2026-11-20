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

## Authorized HA deployment verified
Installed 0.16.4 after an on-host backup of the previous integration and all three Shabbat Flow storage files. Verified archive SHA-256, Python syntax and all 52 installed files; storage bytes stayed identical during replacement. One HA restart loaded the versioned 0.16.4 frontend.

Live verification: the home page displayed a saved browser draft, a scheduled plan observation and a concurrently running climate study independently. All 20 configured rooms remained Ready, and all 20 overview icons contained native SVG graphics. Open saved plan successfully loaded the existing dated household plan without saving or starting anything. Returned to the overview. No device-control activation, study start/stop or notification changes. Active observation records survived restart; this spot check does not prove uninterrupted sampling through the restart gap. Private proof remains outside reusable source.

Archive SHA-256: a1b7f98076e7d406569abca866f4d462f30e46e8c9718e293f9f483ab003e411.
