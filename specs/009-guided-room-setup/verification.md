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

### Installed 0.6.0 verification — 2026-11-18
- Following explicit installation authorization, uploaded the previously tested archive and verified its recorded SHA-256, Python syntax, package path scope and all 30 extracted file contents. Backed up the prior integration and its own stored household settings within HA before extraction.
- Restarted HA after successful configuration validation. Confirmed the running panel serves `/shabbat_flow_static/0.6.0/household.html`, loads existing saved room configuration and exposes all five optional label mappings with live HA label choices and the Tips link.
- No label mappings or household room settings were saved during verification; labels and existing selections remain homeowner-controlled. No device calls or automation edits were performed. Screenshot evidence stays outside the repository.
- Source checkpoint `3880bb9` passed GitHub CI run `44252935456` and was merged to main as `b8e3f75`.

## Version 0.7.0 — bathroom and full lighting changeovers
- Implemented WIZ-FR-022–029, WIZ-NFR-014–015 and CAL-FR-007. Optional dated Shkia/sunset comes from the existing provider. Missing/ambiguous/invalid optional sunset retains daylight lighting and emits a localized warning. Actual provider events, including 1/2/3-day periods, are exercised on both HA versions.
- Bathroom main/night permitted windows are resolved from the dated snapshot and intersected with demand before union. New links default whole-observance; legacy links retain their timing. Optional night switching requires separate selected light sets. Daylight and night fallbacks are visible. General room phases and bathroom-specific policies cannot be enabled together accidentally.
- Room presets support background after recreation/end of evening meal, kitchen main/night/morning, and hallway night lighting. Meal group defaults now connect explicitly opted-in rooms to Family/Hosting meals, including independent power-only or profile HVAC preconditioning. Lunch does not invoke background night demand. Home phases are scoped to explicit availability, including opted-in preparation windows.
- New household workspaces default to no final-boundary shutoff; setting persistence, legacy-client preservation and strict boolean validation tested. Old exports/configurations without the new field retain their behavior. The user's private export was inspected only to diagnose missing transitions and empty meal-group mappings; no household details were copied into tracked files.
- Python unit suite: 65 passed. Node web suite: 27 passed. HA compatibility suites: 63 passed on each of 2026.8.2 and 2026.11.2. Coverage includes interval clipping/empty windows, shared/home union, bathroom daylight/night cycles for 1/2/3 days, DST, missing sunset, exact kitchen/background/hallway transitions, Family/Hosting versus Away/No meal, evening-meal background and final-boundary options. Repository hygiene, generated-package and whitespace checks passed.
- Local browser with fictional fixtures: configured and saved bathroom daylight plus night switching, reopened the saved setup, previewed a three-day main→night→morning→daylight→afternoon cycle without final shutoff (19 events), and verified general kitchen preset controls in Hebrew at 360px. Document scroll width equaled client width (345px); English desktop timeline displayed distinct action badges. Screenshots remain outside the repository.
- Package SHA-256: `30569293a3f664d51a54725b2a2d5bf50080092fc10e1073a1c2fd0c4ba5a5b1`. Packaged but not installed in a household instance in this checkpoint; no production mappings, automations or devices changed. A new workspace is required to use changed settings.
- Existing HA automations are neither suppressed nor claimed by these preview profiles. Overlapping selected demands union: main lighting can remain on while another meal/recreation demand still requires it, even if a background demand has begun. Actual execution and ownership coordination remain deferred.

### Installed 0.7.0 verification — 2026-11-18
- Following explicit authorization, uploaded the tested archive, verified its recorded SHA-256, package scope, Python syntax and all 30 extracted files. Backed up the previous integration and its own household Store inside HA. The stored settings remained byte-for-byte unchanged during installation.
- Restarted Home Assistant and verified the live panel serves `/shabbat_flow_static/0.7.0/household.html`. Existing saved room mappings and completion states loaded. Night/morning/meal presets are present; the final-boundary shutoff control is unchecked by default.
- Verified English and Hebrew setup summaries and automatic Jewish Calendar dates, including the optional dated sunset anchor. Returned the interface to English. No household settings were saved, and no device commands or automation edits were performed for verification. Screenshot evidence stays outside the repository.
- Implementation commit `7d49c31` passed GitHub CI run `44260811893` and was merged to main as `eec8f06`. Existing dated workspaces remain snapshots; use a new workspace after reviewing updated room profiles.

## Version 0.7.1 — actionable room completion feedback
- WIZ-FR-030–031 / WIZ-NFR-016: shared pure validation supplies immediate room-level reasons and the completion gate. Red warning panels with icon/text appear beside room headings, linked areas, review cards and save controls. Valid drafts use amber guidance explaining exclusion from planning until Save & next.
- Inventory review preserves drafts and offers inline refresh. Conflicting saved revisions and offline state explicitly block writes. Server errors persist through failed-save redraws; editing clears obsolete errors while independently active inventory/conflict gates remain. No new dependencies, scheduling changes or household data added.
- 65 Python tests, 30 Node tests and 63 HA tests on each supported HA version passed. Tests cover valid draft versus errors, missing mappings/night lights, dependency completion, inventory review, saved-revision conflict, connectivity, failed persistence, double-submit protection, draft preservation, EN/HE catalogs and 4.5:1 text contrast. Generated assets and repository hygiene passed.
- Local browser with fictional fixtures: observed draft guidance, enabled a night policy with missing night lights, saw the explicit red warning at the room and save controls, verified failed-completion focus, corrected the selection and saved successfully. Verified Hebrew RTL warning presentation. Screenshots remain outside the repository.
- Packaged only, not installed. Existing HA remains on 0.7.0; no live configuration or unsaved browser choices were changed. Archive SHA-256: `1a97e785e9f9ea8d59342a30a813468951ff55f7c6aa51852bd6391651f4d9dd`.
