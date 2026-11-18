# Verification plan and traceability

Status: implementation, automated/local browser checks and installed verification completed through preview 0.5.1. Version-specific evidence is recorded below.

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

## Schedule badge follow-up (previously pending)
WIZ-FR-014 / US5 was not part of the 0.4.0 completion evidence above. Its implementation and verification are recorded below.


## Version 0.5.1 — badge and power-only follow-ups
- WIZ-FR-014: preview events use pure semantic badge mapping. On is green, Off is dark slate, heating/cooling have explicit mode colors, and tracked/unknown actions remain informational. Every badge keeps localized text. Automated contrast tests cover all foreground/background pairs at 4.5:1 or better; presentation mapping does not mutate events.
- WIZ-FR-015–016 / WIZ-NFR-011: dedicated `hvac_power` load/action types permit only `type` and on/off `state`, rejecting temperature, mode, unit and fan overrides. Independent lead time is clamped to the supplied preparation start. UI distinguishes power-only, explicit profile and unscheduled intent. Existing `none` settings are not reinterpreted.
- Native TURN_ON/TURN_OFF flags, including IntFlag values from HA states, are read as diagnostics. Resume semantics remain unverified. No runtime adapter or service/device control calls are added.
- Python suite: 64 passed; Node suite: 25 passed; HA integration suites: 45 passed on each of 2026.8.2 and 2026.11.2. New coverage includes currently-off/heat/cool states with no fan/target metadata, HVAC-only rooms, missing selection, shared/service-only HVAC without a use purpose, missing explicit profile, unchanged legacy intent, preparation-bound clipping, strict action schema, overlap union and conflicting demands.
- Local browser with fictional fixtures: selected and saved power-only for an off unit with missing fan/target metadata, reloaded to verify persistence, and rendered mixed power-only/profile/lighting events. Hebrew mobile preview at 360px had no page-level horizontal overflow; On/Off badges are visually distinct. Power-only notes are concise per event with a single preview-level verification notice.
- Package and repository hygiene checks passed. Full static tree versioned as 0.5.1. Archive SHA-256: `7a9b4983603a3c4105d05d507dbb8eed193ab2a77c48170d8594e583ed1d0314`.
- Bathroom-label candidate filtering remains a separate optional design proposal; it was not promoted to an approved functional requirement in this increment.

### Installed 0.5.1 checkpoint
- Uploaded the archive, verified its SHA-256 and extracted bytes, and retained recoverable copies of the previous integration and its settings inside HA. A normal restart completed after waiting for the preceding startup; the live app served the versioned 0.5.1 static tree.
- Verified the three HVAC intents in the installed editor and power-only summaries with independent lead time. Existing unscheduled selections retained that intent. No household mappings were changed for verification.
- Compiled the installed fictional demo and visually verified green On, dark slate Off and blue explicit cooling badges across lighting and HVAC events. Returned the open app to house setup. Screenshots remain outside the repository.
- GitHub CI passed for implementation commit `cdedc18` (run `44173629881`). Implementation merged to main as `98f691b`.
- Device restoration remains unverified: this release compiles preview intentions only and makes no device-control calls. Existing dated workspaces remain snapshots; changed room setup requires a new workspace.

## Version 0.6.0 — optional label-guided setup
- WIZ-FR-017–021 / WIZ-NFR-012–013 implemented using built-in HA label/area/device/entity registries. Five optional stable-ID mappings are stored in the existing revision-checked settings. Legacy requests retain saved filters; absent filters initialize empty. No runtime dependency or registry/device mutation is added.
- Python unit suite: 64 passed. Node web suite: 27 passed. HA compatibility suites: 46 passed on each of 2026.8.2 and 2026.11.2. Tests cover direct/device memberships, structural revision changes, rename/delete, invalid label IDs, stale writes, reload persistence, legacy requests, label-free defaults, selected exceptions, independent area/label scope, bathroom candidates, area-use suggestions, and unchanged workspace output.
- Local browser with fictional fixtures: mapped all five labels, saved/reloaded, verified separate main/night candidate lists and filtered bathroom areas, and used Show all devices for this room to reveal unlabeled candidates. Label controls stay open while editing. Hebrew at 360px rendered RTL with document scroll width equal to client width (345px); English desktop and Hebrew phone controls visually verified. Screenshots remain outside the repository.
- Added the linked EN/HE in-app Tips page and `docs/setup-tips.md`. Labels are selection aids only; room purposes require explicit application and no device is auto-selected.
- Generated-package, repository hygiene and whitespace checks passed. Archive SHA-256: `f0dea05df9c09344cd5dc8f13236e8f0382ffd473e79322a7f2adefec3cbc4b6`.
- This checkpoint is packaged, not deployed to a household instance. Installed evidence above remains for 0.5.1. No production household settings or HA labels were changed. A subsequent installed refresh/verification must be recorded separately.
