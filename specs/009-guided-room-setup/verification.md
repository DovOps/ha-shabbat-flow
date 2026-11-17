# Verification plan and traceability

Status: implementation and automated/local browser verification completed for preview 0.4.0. Deployment verification is recorded below.

| Scenario / evidence to add | Requirements |
| --- | --- |
| Select rooms, multiple purposes, navigate Back/Next/Skip, summary/Edit | WIZ-FR-001, 002, 011; WIZ-NFR-002, 008 |
| Save, reload/resume, failed write, offline, duplicate submit, concurrent browser revision | WIZ-FR-003, 013; WIZ-NFR-005 |
| Draft/skipped room creates no direct or shared actions; visible exclusions | WIZ-FR-004, 008; WIZ-NFR-006 |
| Area candidates, show all, renamed/moved/deleted/disabled entities | WIZ-FR-005, 013; WIZ-NFR-007 |
| Shared bathroom mapped once, multiple links, removed link, unresolved bathroom | WIZ-FR-006, 008; WIZ-NFR-006 |
| Bathroom intervals overlapping/touching/disjoint; whole 1/2/3-day period; home/away/unset | WIZ-FR-007; WIZ-NFR-006 |
| Copy current heat/cool, off/unavailable/unsupported states, incompatible devices, independent lead time | WIZ-FR-009, 010; WIZ-NFR-003, 007 |
| Legacy settings preserve mappings and semantics; workspace snapshot unchanged | WIZ-FR-012; WIZ-NFR-009 |
| EN/HE catalog parity, RTL, keyboard focus/errors, 360px mobile and desktop | WIZ-NFR-001, 002 |
| Admin access, request limits, own-store-only writes, fictional fixtures, zero device calls | WIZ-NFR-003, 004 |
| Automatic upcoming dates/manual override regression; HA version matrix; versioned package | WIZ-FR-011; WIZ-NFR-009, 010 |

Required commands: Python unit suite, Node web suite, repository hygiene, generated-package check and both supported HA integration suites. Record counts and live verification only after executing them.


## Executed checks
- Python unit suite: 62 passed.
- Node web suite: 23 passed, including wizard write freezing, double-submit guard, failed-save preservation and unresolved-bathroom gating.
- HA 2026.8.2 and 2026.11.2: 41 integration tests passed on each version. Added tests cover schema migration, legacy selections without mappings, draft persistence through integration reload, unfinished-room exclusion, sanitized nonstructural HVAC telemetry, explicit home/away/unset policies, overlapping/touching/disjoint bathroom demand and whole-observance behavior for 1/2/3 days.
- Generated package, repository hygiene and whitespace checks passed. No new external dependencies.
- Local browser with fictional fixtures: selected a room, linked/configured a bathroom, saved the bathroom, resumed the unfinished room after reload, copied current heating/target/fan settings and reviewed the summary. English and Hebrew journeys rendered correctly. At a 360px viewport, the Hebrew summary and room editor had no page-level horizontal overflow; focus moved to the step heading after navigation.

## Scope and limits
- The installed integration remains preview-only. No device execution, automation activation or household inference.
- Current HVAC copying requires supported compatible heat/cool, target and fan values. Unsupported metadata needs explicit adjustment or opting out. Recent-use ranking remains deferred.
- Saved settings resume at the first unfinished selected room rather than persisting an exact viewport or cursor position. Back navigation retains in-memory edits; Save & next, Save progress and Skip persist them.
- Legacy selected rooms with no mapped devices migrate to unfinished. Existing configured rooms retain their original shared use-window policy. Migration is persisted only on an explicit settings save.
- No real mappings were written for browser verification. Browser persistence flows used fictional local fixtures; HA persistence was verified in isolated integration tests.
- The UI renders only the active room's detailed controls; a dedicated performance benchmark at the maximum supported inventory size is not yet recorded.


## Installed verification and checkpoint
- Uploaded the built 0.4.0 archive, verified its SHA-256 and every extracted file, and kept recoverable copies of the previous integration and this integration's settings inside HA. No home data was exported into the repository.
- Verified the versioned installed wizard after restart: existing selections are retained, unmapped legacy selections resume as unfinished, one room is displayed at a time, and English/Hebrew navigation renders correctly.
- Verified the summary still loads the upcoming period and its dated candle-lighting, sunrise and end from the installed Jewish Calendar.
- An initial deferred restart was declined because another core job was running. A normal restart after startup completed succeeded; the corrected migration was then visibly verified.
- GitHub CI passed for implementation commit `f1bfc18` (run `44165028408`); implementation merged to main as `bc297ae`. Final verification recorded in this documentation checkpoint.
- Final archive SHA-256: `c940b3a3eafa6d606d5890aff15570063dcc841ba688bd13ff5e91055efba422`.
