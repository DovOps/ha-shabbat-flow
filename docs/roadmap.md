# Product requirements and roadmap

All stages inherit English/Hebrew and RTL parity, offline planning, contributor household-data separation and explicit activation requirements. This is a general product, not a copy of one household's records.

## R1: local preview (current feature 001)
Fictional configurable rooms/resources, meal choices, independent climate/lighting offsets and homeowner-selected bedroom sleep-light cutoff, shared dependencies, explicit dated candle-lighting/sunrise/end inputs, multilingual timeline, validation, browser-local drafts and JSON export. No HA access or execution.

## R2: Home Assistant discovery and preview integration
Before hardening the integration, implement continuous multi-day planning from `specs/003-multiday-observance/spec.md`, alongside homeowner-defined schedule groups as specified in `specs/002-extensible-schedule-groups/spec.md`. Lighting and HVAC become presets over a generic schedule model. Include track-only groups and references to existing scenes/scripts; specialized appliance/cycle/elevator capabilities must be explicitly supported and approved, never inferred from on/off availability.
Read areas/entities and automation definitions using supported APIs; owner-confirm physical load/alias mappings. Guided setup in both languages; reference existing scenes/scripts and flag conflicting ownership. Build a native dashboard card and authenticated backend, with revision-aware household plans and administrator activation permissions. Calendar adapter snapshots verified local zmanim. Maintain a tested HA compatibility matrix. No Good Days dependency or compatibility commitment has been adopted; third-party proposals require review.

## R3: controlled execution
Detailed draft: [Feature 010 specification](../specs/010-controlled-execution/spec.md) and [implementation plan](../specs/010-controlled-execution/plan.md). Observe-only persistence, sampled comparison and a bounded unmanaged-automation overlay are implemented and deployed in 0.12.1; device execution remains unimplemented.
Approve/freeze before earliest preparation event; policies for late edits and missing plans. Persist event outcomes, deduplicate actions, use absolute instants, bound retries, reconcile permitted current states after restart without replaying stale events. Separate per-bedroom temperatures, fan modes, pre-conditioning and wake/off rules from shared-space HVAC and lighting. Test recovery, rollback and offline operation before a weekday pilot and shadow Shabbat.

Existing boiler automations stay available. Owner-approved keep/suspend/activate windows snapshot prior enabled states and restore only what the planner changed, with intervening owner changes respected. Suspension is not a boiler-off command and may not stop an already running automation. Existing outdoor nightly 23:00 catch-all has one owner; one-night extension delays off, expires after the night and must not race the original rule.

## R4: profiles and observance expansion
Model sleeping and recreation as separate time-bounded room uses; allow both for the same room. Early/Standard/Late sleeping profiles adjust HVAC preparation, sleep lighting and wake/off independently without storing age or identity. HVAC includes heating and cooling with explicit supported mode/temperature selections. See feature 002 for the model; feature 001's room selector means sleeping only.
Morning/lunch/nap profiles; seasonal and late-friends fixed-time overrides; entry night scene; selective night-scene suppression; per-room sleep/wake controls. Handle consecutive Shabbat/Yom Tov days without intermediate false shutdowns. Local observance settings and end-boundary conventions are explicit. Special high-attendance prayer-service profiles are separate from residential defaults. No religious-policy inference.

## R5: feedback and historical analysis (phase-two capability)

Detailed requirements: `specs/004-feedback-loop/spec.md`. Start with optional 1–5 ratings and manual planned-versus-reported review tied to immutable plan revisions; add observed-history comparisons and trends when coverage is available. Proposals modify future drafts only after owner acceptance.
Post-observance multilingual feedback: actual rooms/meals, comfort by room/time, pre-conditioning, HVAC-off/wake, lighting changes, bathrooms/access, mornings, outdoor extension, interventions, what worked and one-time versus recurring requests. Compare versioned planned actions, actual observations and feedback. Codex proposes evidence-backed changes; owners approve new versions.

Read-only history import reports retention and coverage first. Deterministic snapshot-based metrics: transitions, duration, first/last use, censored intervals, sustained versus brief task lighting, co-activation, overlap and lead/lag. Deduplicate synchronized entities before correlation. Preserve missing/unavailable periods and context-attribution uncertainty; missing user ID never proves physical switching. Assisted-operation context is optional and not a religious-identity field. Correlation proposes groups/windows, never infers household identity or occupancy. Show sample size, evidence and uncertainty; identical inputs/settings produce identical results. Annual events are not ordinary-weekend training data.

## R6: reusable onboarding
Validated configuration import/export, synthetic example homes, optional sanitized inventory export and AI configuration-assistance prompt. Generated proposals use the same schema/compiler and remain drafts. Automatic conversion of arbitrary existing automations and optional messaging channels are deferred.

## R7: optional MCP/chat interface
See `specs/005-chat-interface/spec.md`. Offer plan inspection, future-draft editing, feedback and proposal review through the same application services as the dashboard. Evaluate HA-native MCP exposure first; no dependency is selected. Initial scope excludes activation and direct device control.

## Decisions still open
License choice before public release; provider-specific HVAC qualification; temperature limits; remaining household defaults and override lifecycle. Feature 010 records accepted native execution direction, admin activation, preparation deadline, retry/grace and retention defaults; implementation and qualification remain separate gates. No unknown value is silently promoted to an approved default.

### Approved next iteration: bedroom rest schedules
Feature 009 US12 adds optional daytime naps and independent late wake-up/HVAC-off choices per bedroom and dated day. Nap HVAC is separate from overnight lighting, supports preconditioning and preserves settings when requested; overlapping compatible demands keep units running continuously. Implemented, tested and deployed in 0.10.0; see checkpoint-010. Subsequent circulation and independent meal-HVAC settings were deployed in 0.11.0.

### Existing automation schedule overlay (approved specification)
Read-only forecasts for time/sun-based HA automations and conditions/triggers on the known mapped issur-melacha state. Show source badges and possible planner conflicts without changing automation ownership. Unsupported or unresolved schedules stay explicit. See MD-FR-020–022 and MD-NFR-009; literal time/sun triggers, weekday conditions and supported On/Off actions are implemented and deployed in 0.12.1. Issur-melacha conditions/triggers, arbitrary scripts and full ownership handoffs remain pending.

## Immediate validation path
See [prediction-only weekend and go-live gates](dry-run-to-live.md). This is a staged review plan: freeze exports, compare normal observed behavior and feedback, complete the specified executor, run authorized weekday/recovery tests, then explicitly arm a limited validated scope. The current preview remains non-executing.

## Current requirement and release coverage
See [requirements status](requirements-status.md) for the maintained feature map. Hourly thermal evidence and EN/HE visual observation reports are implemented/tested and deployed in 0.13.0. Live observation collection and real-data report review remain pending.

Observe 0.13.0 report additions: zones ranked by minute sampled On duration, combined all-zone hourly table, and aligned planned room-use/planned-light/observed-light bands. Missing time remains unknown. Implemented/tested/deployed in 0.13.0; real observation review remains pending.

## Standalone climate studies (0.14.0, deployed)
Feature 011 adds manual 1–48-hour studies without a Shabbat plan, selected zones/lighting, optional room reference sensors, read-only persistence and dedicated reports. Automated tests and fictional EN/HE review complete; real collection and PDF pagination pending. Scheduled starts and automatic summary delivery are future scope. Installed HA is 0.14.0; live setup/source discovery verified. No study started.

The same 0.14.0 package includes explicit room light/switch activity signals and distinct observed switch timelines. Both On and Off changes are evidence, never confirmed occupancy or manual operation.

0.14.1 adds room-scoped Select all / Clear all for climate-study activity signals. Implemented/tested, not yet deployed; HA remains 0.14.0.

## Settings and optional notifications (0.15.0)
Feature 012 implements dependency discovery, explicit SMS/Companion App lifecycle notifications and configurable pre-candle push reminders. Tests pass; deployed 0.15.0 with capability detection and disabled defaults verified. User-configured delivery and mobile report export are next validation steps. This does not implement scheduled climate studies, public report hosting, message replies or device execution. Existing execution qualification/activation/recovery roadmap remains unchanged.

## Documentation and brochure website
Feature 013 adds a local Docusaurus preview and GitHub Actions publication at the repository's Pages path. English/Hebrew visitor content and generated English specs share canonical repository sources. Public launch follows owner-controlled repository visibility and Pages setup; official HA verification and HACS inclusion are not claimed.

Documentation follow-up adds a prominent coding-agent/spec-driven developer guide and reviewed actual-interface gallery. Display name becomes Shabbat Flow with release limits shown separately. App navigation/status tile updates are included in packaged 0.15.1; production upgrade remains separate.

0.16.0 local checkpoint: EN/HE workflow gallery and room-option guide; selected-option inline explanations; HA icon metadata/fallback presentation; additive clock/sunrise nap and wake defaults, day-end naps and HH:MM lighting/rest offsets. Implemented and packaged locally; HA remains on 0.15.0. Native HA icon rendering and production UI installation are not yet live-validated. No execution or device-control changes.

0.16.1: clean existing-automation schedule and friendly grouped events delivered locally. Scheduled clock/sun and bounded registry-identified issur transitions supported; arbitrary calendar events/templates remain collapsed diagnostics, not guessed events. Device execution and production HA installation remain separate. Public documentation publication at dovops.io/ha-shabbat-flow authorized.

## Current HA deployment — 0.16.1
The owner-authorized upgrade is installed and the live panel verified after one restart (checkpoint 019). This supersedes earlier packaged/not-installed notes for 0.14.1–0.16.1. Saved household setup and notification choices were retained. Native HA icon elements, new navigation and dependency status presentation were verified live. Real-plan forecast accuracy, real-study reports and future device execution remain separate validation/implementation work. Public EN/HE documentation is live at https://dovops.io/ha-shabbat-flow/.

## 0.16.2 — study responsiveness and presentation
CS-FR-011/CS-NFR-007: targeted zone updates, preserved selections and lazy 50-item other-area batches implemented and locally tested with 100 zones/2,000 signals. UI-FR-006/UI-NFR-003: start-aligned icon/name groups, cached HA-owned SVG graphics and timeline labels. WEB-FR-012: fictional EN/HE Settings gallery and prominent current observe/future control scope. See checkpoint 020. Packaged; HA remains 0.16.1 pending installation and live freeze/icon validation.

## 0.16.3 — climate setup clarification
CS-FR-012/CS-NFR-008 and UI-FR-007 implemented: built-in A/C room-temperature default, optional additional comparison sensor, adjacent logical-start checkbox/icon/name layout, and retained locale selections. Verified with fictional large inventory and native sampling test. See checkpoint 021. Packaged, not installed; HA remains 0.16.1.

0.16.3 deployment completed: corrected versioned frontend URL, native SVG graphics, responsive tested zone/language interaction and EN/HE alignment verified live. Supersedes packaged-only notes above. Release marker consistency is now enforced during packaging and HA lifecycle tests. See checkpoint 021; real study/report validation and future device execution remain separate.

## 0.16.4 — easier setup and visible study status
Implemented/tested: automatic simple-day Home from explicit room/nap/home-meal choices, top/bottom green planner actions, compact room-status links and main-page plan/observation/climate-study overview. Custom partial-day availability remains deliberate review; saved drafts are identified as browser-local and are not activation. Package ready; no HA upgrade performed. HA remains 0.16.3. Next: authorized installation and validation against real saved plans/concurrent observation runs; execution roadmap remains separate.

0.16.4 deployment verified: backed-up replacement, 52-file parity, three retained stores, one HA restart, live saved-plan reopening and concurrent plan/climate status display with 20 native room icons. Supersedes the packaged-only state above. No device controls enabled; see checkpoint 022.

Brochure gallery now includes 0.16.4 home activity and room-readiness examples in English/Hebrew, using fictional data. Website-only publication; no HA installation needed.

PDF performance first step: print-only Arial/Tahoma preference implemented and bilingual embedding inspected. Next: install in a separately authorized upgrade, export a full report and compare phone rendering. Gradient/chart optimization remains a separate potential follow-up, not part of this change.

PDF font deployment: authorized static-only patch installed on 0.16.4 with seven-file checksum parity and backups; no HA restart or observation interruption. Supersedes the not-installed font note above. Browser cache marker added; phone performance comparison remains pending.

Next planning extension: feature 014. Deliver fixed meal/activity/service lighting controls first, independent fan/outlet previews next, then temperature-policy shadow replay and feedback classification. Keep first-live fixed-device qualification under feature 010 separate from conditional comfort and appliance execution. Do not turn an exceptional early meal into a global timing change. All new feature-014 requirements are specified, not implemented/deployed.


## 0.17.0 — flexible activities and comfort shadow policies
Feature 014 planning/observation stages implemented: explicit meal durations and cleanup, independent room playtime/recreation, per-load exclusions/replacement, service-light presets and calendar offsets, bathroom daylight suitability, fan/outlet track-only mappings, temperature-policy shadow sampling, and classified feedback in EN/HE HTML/PDF summaries. Existing saved plans retain their original schedules until edited. No live adapters or device calls added. Feature 010 qualification, provider freshness/manual holds, hardware resume tests and full mobile/PDF acceptance remain pending. Supersedes feature 014's specified-only status above. See `specs/014-flexible-activity-comfort/verification.md` and checkpoint 023 for actual test/deployment evidence.

0.17.0 deployment verified: 55 packaged files, three retained stores, one backend restart, saved-plan reopening and meal-preset preview. Device control remains unarmed; household acceptance and execution qualification are pending. See checkpoint 023.
