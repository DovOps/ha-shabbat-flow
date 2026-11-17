# Checkpoint 002: configurable multi-day preview

Branch: `002-planning-foundation`. Local preview only; no Home Assistant changes.

## Try it
Run the server from README.md and open http://127.0.0.1:8765/v2 . The original page links to it. The fictional three-day example shows separate sleeping and recreation sections, editable per-room profiles, per-day meal choices, full-period home/away windows and a combined preview timeline. Change a sleeping profile and compare its HVAC/light cutoffs; add a recreation use for the same room in a different window. Overlapping room windows remain explicit conflicts.

Edit supplied calendar anchors and boundaries together when adding/removing a day. This prototype does not calculate actual holiday dates or zmanim. Profile and group rule editing is currently advanced JSON with validation before application. Keep real household drafts/exports outside the repository.

## Included
- Pure bounded calendar/room-use validators and generic binary/HVAC schedule compiler.
- Maintained shared-load demands, cross-group conflicts, physical aliases and ownership checks.
- Track-only intentions, separate HVAC/light timing, explicit heating/cooling settings.
- Multilingual EN/HE v2 interface, separate browser draft key, preview export.
- Future specifications for feedback/ratings/improvement and optional MCP/chat, with no new dependency selected.

## Verification and limits
70 automated tests pass (61 Python, 9 Node). Repository hygiene and syntax checks pass. Browser interaction, RTL and responsive visual checks remain pending after the earlier browser-access denial; these are not represented as verified. No activation or HA connection exists. See feature 002 analysis.md and tasks.md for unfinished work.

User authorized continuing local checkpoint commits on this branch. Pushes remain separate. The next work is guided profile UX, copy-day/migration with review, browser verification, and feedback storage; HA provider selection/execution require their own review.
