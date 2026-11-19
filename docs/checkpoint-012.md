# Preview/observe 0.12.0

Accepted Feature 010 defaults and implemented an observe-only foundation. No live approval/arming endpoint, service adapter, device call or automation mutation was added. No production install or observation run was started. The frozen plan remains a prediction, not execution evidence.

Included: server recompilation and immutable plan copies; atomic integrity-checked local persistence and explicit write-failure behavior; admin-only idempotent start, overlapping observation rejection, stop/configure/export; one-minute background sampling, per-event sampled outcomes, separate power/HVAC-settings comparison, unknown restart gaps, bounded retention/records and report-only recovery checks. EN/HE controls include start, summary and combined plan/observation JSON download. Initial unavailable HVAC preserve-settings baselines remain unknown.

Unmanaged forecasts cover literal fixed-time and HA sun triggers, weekday-only conditions, bounded delays and direct entity On/Off calls. They are interleaved with planned events in HTML and inherited PDF output, with separate source labels and conflict diagnostics. Unsupported state/issur conditions or triggers, templates, scripts and dynamic targets remain unresolved. No forecast grants live ownership clearance or changes chart demand semantics. Full automation overlay/ownership scope is not complete.

Recovery checks default to enabled report-only, five-minute boot delay and 30-minute repetition, configurable/disableable per run. Future corrective recovery is specified with continuing ownership, prior confirmed planner action, persistent cooldown/budget, override/handoff and expiry protections; it is not implemented here.

Verification: 76 Python foundation/compiler tests, 41 Node tests and 90 HA tests on each of 2026.8.2 and 2026.11.2 passed. New tests cover persistence/restart, corrupt/disk-error behavior, no-service-call boundary, idempotence/overlap, policy bounds/disable, mapping invalidation, sampled coverage totals, HVAC settings versus power, source uncertainty/DST, interval conflicts, authorization, bilingual labels and interleaved source badges. Generated-package and repository checks passed. Browser interaction and exported PDF pagination remain unverified; the current HA installation remains the preceding release.

## Deployment and compatibility patch — 0.12.1

Authorized HA deployment completed after backing up the prior integration and household store. All 36 installed package files matched the archive, Python sources parsed, and saved household bytes were unchanged. HA restarted and served the versioned 0.12.1 panel. No observation was started and no device or automation control was activated.

Live read-only verification exposed editor metadata and literal label targets as unsupported. EX-FR-034 / EX-NFR-015 now cover metadata acceptance, HA-native target expansion and membership fingerprints. The patch was verified with synthetic registry membership/missing-label/mixed-domain tests and zero service calls. 76 compiler tests, 41 Node tests and 91 HA tests on each supported version passed; package, hygiene and whitespace checks passed.

The installed preview showed chronologically interleaved fixed-time outdoor Off, pre-sunrise hallway Off and sunset outdoor On events as unmanaged. Unsupported state/issur conditions and scripts remain explicit unresolved sources. Charts continue to show planner demand only. Observation persistence/restart is tested in the harness; a real weekend run and exported PDF pagination remain pending. Private room settings and screenshots are excluded from this repository.
