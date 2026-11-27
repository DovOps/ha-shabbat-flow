# Requirements and rollout status

Updated 2026-11-20. This index maps current product scope to its authoritative specifications and checkpoint evidence. It is a feature-level consistency review, not a claim that every acceptance criterion has been independently re-tested. Historical checkpoint documents retain their original verification results.

| Scope | Specification | Current status / evidence |
|---|---|---|
| Candle-lighting offsets, independent lighting/HVAC, multilingual EN/HE/RTL | [001](../specs/001-preview-planner/spec.md), [002](../specs/002-extensible-schedule-groups/spec.md) | Core implemented and tested; some full browser/accessibility checks remain open in tasks. |
| Generic groups, sleeping vs recreation, track-only intent | [002](../specs/002-extensible-schedule-groups/spec.md) | Preview implemented; arbitrary scene/script/cycle execution and v1 migration pending. |
| 1–3-day Shabbat/Yom Tov, Israel/diaspora, per-day meals and copy-day | [003](../specs/003-multiday-observance/spec.md), [008](../specs/008-automatic-zmanim/spec.md) | Compilation/provider preview implemented; no automatic live activation. |
| Family feedback, ratings, historical analysis and recommendations | [004](../specs/004-feedback-loop/spec.md) | Broader workflow specified, not implemented. Feature 010 provides sampled observation evidence, not the complete feedback/history-analysis feature. |
| MCP/chat | [005](../specs/005-chat-interface/spec.md) | Future specification; no MCP server or chat activation adapter. |
| HA integration, registry synchronization, automatic Jewish Calendar/manual override | [006](../specs/006-installable-preview/spec.md), [007](../specs/007-ha-household-sync/spec.md), [008](../specs/008-automatic-zmanim/spec.md) | Implemented/tested/deployed; see respective task/verification records. |
| Wizard, labels, bedrooms/common areas/bathrooms/hallways, shared bathrooms | [009](../specs/009-guided-room-setup/spec.md) | Implemented/tested/deployed; installer chooses labels and actual entities. |
| Night/morning/daylight policies, meal HVAC, naps/late wake, afternoon hosting, access lights, opt-in final shutoff | [009](../specs/009-guided-room-setup/spec.md) | Implemented/tested/deployed through 0.11.0. Exported PDF pagination QA is not complete for every combination. |
| Persistent observe runs, exports, report-only recovery | [010 EX-FR-030–033](../specs/010-controlled-execution/spec.md) | Implemented/tested/deployed in 0.12.1; real weekend observation validation pending. No run started by deployment. |
| Existing automation forecast | [003 MD-FR-020–022](../specs/003-multiday-observance/spec.md), [010 EX-FR-032/034](../specs/010-controlled-execution/spec.md) | Bounded time/sun/weekday and direct or literal registry targets deployed. Issur conditions/triggers, scripts and complete ownership/handoffs pending. |
| Hourly temperatures, mode/action, outdoor source, gaps/provenance | [010 EX-FR-035–037 / EX-NFR-016](../specs/010-controlled-execution/spec.md) | Implemented/tested/deployed in 0.13.0; live observation validation pending. 94 HA tests on each supported version in checkpoint-013. |
| Thermal charts, active-zone ranking, combined hourly table, use/light bands and printable summary | [010 EX-FR-038–041 / EX-NFR-017–019](../specs/010-controlled-execution/spec.md) | Implemented; fictional EN/HE visual review. Installed HA is 0.14.0; live weather selector and observe controls verified. Native print/PDF pagination and real-data review remain pending. |
| Standalone 1–48-hour climate studies, optional reference sensors and room light/switch activity signals | [011 CS-FR-001–010 / CS-NFR-001–006](../specs/011-climate-studies/spec.md) | Implemented/tested/deployed in 0.14.0; live study setup and light/switch source discovery verified. Room-scoped bulk selection implemented/tested in 0.14.1, not yet deployed. Real study and PDF pagination pending. |
| Approval/arming/disarm, device adapters, corrective restart recovery | [010 EX-FR-001–029](../specs/010-controlled-execution/spec.md) | Specified and defaults accepted; live execution unimplemented. HVAC resume qualification and authorized weekday tests required. |
| Boiler suspension/restoration and outdoor extensions | [002](../specs/002-extensible-schedule-groups/spec.md), [010](../specs/010-controlled-execution/spec.md), roadmap | Future controlled execution scope; existing automations remain independently active. |

## Checkpoint rule
Update FR/NFR, plan, tasks and evidence in the same change. Update this table and roadmap when status changes. Record packaged vs installed versions separately. Do not promote simulated or fictional evidence to household validation. Preserve pending tasks rather than checking them off to match a release headline.

## Latest review corrections
- Corrected stale roadmap statements about deployed bedroom rests and the partial automation overlay.
- Corrected Feature 003's stale provider/copy-day status and Feature 002's provider-spike task reference.
- Removed an unadopted third-party compatibility promise from the roadmap; dependencies still require owner review.
- Kept feedback/MCP/live execution, full condition forecasting and remaining manual QA explicitly pending.

## Feature 012 — Settings, notifications and reminders (0.15.0)
SN-FR-001–010 / SN-NFR-001–006 implemented and tested: discovery-based optional SMS/app channels; private lifecycle settings; secure retained-report links; durable per-channel attempts; dedicated dependency Settings; multiple same-local-day pre-candle push reminders guarded by explicit issur Off and provider calendar coverage. Tests in `tests/ha/test_notifications.py` plus existing observer, renderer/catalog and auth suites. Both channels and reminders default off. Deployed 0.15.0 with live capability/default-off UI verified; real delivery, enabled reminder behavior and mobile report/PDF validation remain pending. No device control enabled.

## Feature 013 — Public documentation website
WEB-FR-001–006 / WEB-NFR-001–004: Docusaurus brochure, EN/HE guides and RTL, generated canonical technical reference, manifest-driven version, local preview and gated GitHub Pages workflow implemented. Public publication remains pending owner visibility/Pages enablement. The site describes the actual custom-integration preview and separates planned execution from current capabilities; no official HA verification claim.

Website follow-up: WEB-FR-007–009 / WEB-NFR-005 add agent-assisted developer onboarding, root AGENTS.md guidance, a fictional-data actual-interface gallery, EN/HE captions and active navigation. UI-FR-001–003 / UI-NFR-001 specify Shabbat Flow naming, app navigation and lime/amber/neutral dependency tiles. HA 0.15.1 presentation changes are packaged for a future install; installed HA remains 0.15.0 until explicitly upgraded.

0.16.0 local checkpoint: EN/HE workflow gallery and room-option guide; selected-option inline explanations; HA icon metadata/fallback presentation; additive clock/sunrise nap and wake defaults, day-end naps and HH:MM lighting/rest offsets. Implemented and packaged locally; HA remains on 0.15.0. Native HA icon rendering and production UI installation are not yet live-validated. No execution or device-control changes.

0.16.1: existing-automation forecast scope, grouped friendly-name/device-icon presentation and collapsed print-excluded diagnostics implemented/tested. Reactive sources remain in ownership audit; no execution clearance. Public Pages publication at https://dovops.io/ha-shabbat-flow/ authorized after repository visibility changed; deployment verification recorded in checkpoint 019. HA package remains a separate, not-yet-installed update.

## Current HA deployment — 0.16.1
The owner-authorized upgrade is installed and the live panel verified after one restart (checkpoint 019). This supersedes earlier packaged/not-installed notes for 0.14.1–0.16.1. Saved household setup and notification choices were retained. Native HA icon elements, new navigation and dependency status presentation were verified live. Real-plan forecast accuracy, real-study reports and future device execution remain separate validation/implementation work. Public EN/HE documentation is live at https://dovops.io/ha-shabbat-flow/.

## 0.16.2 — study responsiveness and presentation
CS-FR-011/CS-NFR-007: targeted zone updates, preserved selections and lazy 50-item other-area batches implemented and locally tested with 100 zones/2,000 signals. UI-FR-006/UI-NFR-003: start-aligned icon/name groups, cached HA-owned SVG graphics and timeline labels. WEB-FR-012: fictional EN/HE Settings gallery and prominent current observe/future control scope. See checkpoint 020. Packaged; HA remains 0.16.1 pending installation and live freeze/icon validation.

## 0.16.3 — climate setup clarification
CS-FR-012/CS-NFR-008 and UI-FR-007 implemented: built-in A/C room-temperature default, optional additional comparison sensor, adjacent logical-start checkbox/icon/name layout, and retained locale selections. Verified with fictional large inventory and native sampling test. See checkpoint 021. Packaged, not installed; HA remains 0.16.1.

0.16.3 deployment completed: corrected versioned frontend URL, native SVG graphics, responsive tested zone/language interaction and EN/HE alignment verified live. Supersedes packaged-only notes above. Release marker consistency is now enforced during packaging and HA lifecycle tests. See checkpoint 021; real study/report validation and future device execution remain separate.

## 0.16.4 — presence defaults, setup shortcuts and activity overview
Implemented and tested: MD-FR-023–024/MD-NFR-010 (explicit room/nap/home-meal choices set simple day Home; preserve custom windows), UI-FR-008–010/UI-NFR-004 (shared green planner actions, room-status links, browser-draft versus persisted plan/climate-run status). English/Hebrew, no device commands or implicit activation. Verification: 77 core, 58 JS and 112 HA tests on each supported version; local EN/HE visual and shortcut checks. Package 0.16.4; HA remains 0.16.3 pending separately authorized installation. See checkpoint 022.

0.16.4 deployment verified: backed-up replacement, 52-file parity, three retained stores, one HA restart, live saved-plan reopening and concurrent plan/climate status display with 20 native room icons. Supersedes the packaged-only state above. No device controls enabled; see checkpoint 022.

Brochure gallery follow-up: WEB-FR-013/WEB-NFR-005 adds four 0.16.4 screenshots (home activity overview and room readiness, EN/HE) from an opt-in fictional loopback fixture. Actual UI captures, descriptive captions/alt text and documented provenance; no household data or HA runtime changes.

PDF font follow-up: MD-FR-025/MD-NFR-011 implemented locally. Fictional bilingual Chrome comparison confirms Arial embedded TrueType subsets versus system-font Type 3 glyphs. Screen fonts and charts unchanged. Not installed in HA; full-report phone performance remains unverified. See pdf-font-verification.md.

PDF font deployment: authorized static-only patch installed on 0.16.4 with seven-file checksum parity and backups; no HA restart or observation interruption. Supersedes the not-installed font note above. Browser cache marker added; phone performance comparison remains pending.

Feature 014 (AC-FR-001–014 / AC-NFR-001–006): specified/planned only. Adds meal-duration presets, recreation/playtime windows, subgroup and service schedules, explicit bathroom daylight suitability, per-activity HVAC/fan policies, temperature-gated shadow evaluation and outlet appliance semantics. Extends existing generic schedule/feedback contracts; no new runtime behavior or deployment. Household observation and feedback remain private. Conditional HVAC/fan/appliance execution must not be treated as supported by the current observe-only implementation.


## 0.17.0 — flexible activities and comfort shadow policies
Feature 014 planning/observation stages implemented: explicit meal durations and cleanup, independent room playtime/recreation, per-load exclusions/replacement, service-light presets and calendar offsets, bathroom daylight suitability, fan/outlet track-only mappings, temperature-policy shadow sampling, and classified feedback in EN/HE HTML/PDF summaries. Existing saved plans retain their original schedules until edited. No live adapters or device calls added. Feature 010 qualification, provider freshness/manual holds, hardware resume tests and full mobile/PDF acceptance remain pending. Supersedes feature 014's specified-only status above. See `specs/014-flexible-activity-comfort/verification.md` and checkpoint 023 for actual test/deployment evidence.

0.17.0 deployment verified: 55 packaged files, three retained stores, one backend restart, saved-plan reopening and meal-preset preview. Device control remains unarmed; household acceptance and execution qualification are pending. See checkpoint 023.

## 0.18.0 — Reports and guided planning
Feature 015 implements top planner commands, collapsed optional controls, Reports archive, deterministic sampled agreement summaries and persisted owner reviews in EN/HE. Reports are available for every recorded period; no automatic observation or device control is started. Review text/ratings inherit 20-run/90-day retention; writes use atomic persistence and revision checks. HTML/PDF/JSON include reviews. Feature 004 remains partial: multi-person feedback, comparable trends and automatic proposal application are future work. Deployment and validation evidence: checkpoint 024.

0.18.0 deployed and live-read validated: retained archive, completed report and saved setup available after one restart; device control remains off. See checkpoint 024.

Feature 016 stored PDF downloads: implemented and deployed after owner approval of the renderer dependencies; see specs/016-stored-pdf-downloads.

## 0.19.0 — lazy stored PDFs
Feature 016 implemented and locally tested. PDFs are generated on demand from JSON, stored privately and reused while unchanged. Admin-authenticated download/open/share flow replaces reliance on mobile print; original browser print remains available. Rendering runs separately from observation; no device control. Supersedes the dependency-pending status above. See checkpoint 025; deployment/phone acceptance are recorded separately.

0.19.0 deployed: retained observation PDFs generated and downloaded in both languages through authenticated HA. Source stores preserved, no controls activated. Desktop download passed; mobile Open/Share awaits user acceptance.

0.19.1 deployment verified: the final 66-file patch preserved all three saved stores, then a second backend restart loaded the versioned 0.19.1 UI. A retained completed report generated successfully and exposed Download, Open and Share commands. No observation or device control was activated. Both supported-version test suites and branch CI passed. Real phone acceptance remains pending.

## 0.19.2 — permanent room fan assignments
Feature 017 adds optional room Fans mappings and configurable entity/device label filtering. New dated plans inherit fan loads; explicit activity windows define their timing, separately from HVAC. Migration leaves old setups unselected and old plans untouched. Native fan and switch domains supported; preview/observation only. See checkpoint 026 for verification and deployment status.

0.19.2 installed and live-read verified after one restart. Existing saved setups preserved; Fans selector available with no automatic assignments. See checkpoint 026.

## Feature 018 — away defaults and lighting execution pilot (0.20.0)
GO-FR-001–009 and GO-NFR-001–004 are implemented for a deliberately limited lighting pilot. Away day choices clear irrelevant meals; complete previews have a separate device review, approval and Schedule and observe step. Saved drafts cannot activate themselves. Live dispatch is limited to explicitly reviewed light/switch lighting roles with weekday verification notes, conservative writer checks, state-aware On/Off, durable intent and bounded optional correction. HVAC, fans/appliances, external handoffs and automatic retries remain excluded. Broader Feature 010 acceptance is not marked complete. Verification/deployment evidence: checkpoint-027 and Feature 018 verification. No production plan is armed by deployment.

## Feature 019 — exact-plan rehearsal (0.21.0)
RH-FR-001–008 and RH-NFR-001–003 implemented with deterministic compiled moments, explicit area/device scope, simulation, separately confirmed binary-lighting tests, independent persisted evidence, reviewed context-aware restore, and feedback/export. HVAC/fans/appliances remain simulation-only. No automatic replay, restoration or weekend activation. Automated verification is complete; UI visual acceptance, installation and owner-supervised hardware tests remain pending. See Feature 019 verification and checkpoint 028.


Deployment verified after access was restored: 71 packaged files byte-verified, three existing saved-data files preserved unchanged, on-host integration/storage backup, and one HA restart. The versioned 0.21.0 UI loaded with all 20 saved rooms ready. Exact-plan scenario discovery and read-only simulation succeeded against an existing saved plan; no rehearsal was applied and no control run was scheduled. Fictional EN/HE layout, area selection, simulation and keyboard activation were checked. Owner-supervised physical tests and mobile acceptance remain pending. Both GitHub checks and website publication passed for the implementation commit.


## Feature 020 — nap feedback and HVAC/fan rehearsal (0.22.0)
CF-FR-001–007 / CF-NFR-001–003 implement visible short-day nap clipping, adjacent timing errors, explicit private mode/speed capture and rehearsal-only HVAC/fan power with settings verification and reviewed restore. Scheduled eligibility stays lighting-only. Fan assignments require explicit activity events. No automatic hardware qualification, thermostat calibration or appliance actuation. Deployment and acceptance evidence: checkpoint 029.

0.22.0 installed and read-only verified: nap creation with boundary feedback, HVAC planned-state review and missing-baseline safeguard. Saved data preserved; no devices actuated or schedules armed. Owner-supervised HVAC/fan preservation and restore acceptance remain pending.

## Feature 021 — adoption playbook
AP-FR-001–005 / AP-NFR-001–003: shared EN/HE public and bundled guide, app navigation/contextual rehearsal help, gradual adoption gates, explicit capture/restore semantics and current eligibility limits implemented. Installed as a 0.22.0 static documentation patch without restart, saved-data changes or device control. Cached entry pages may need refresh; direct guide verified. Phone/print acceptance remains pending. See checkpoint 030.

Planner-blocker callouts (UI-FR-011–012/UI-NFR-005): implemented locally with top/bottom alert panels, room/device context and repair/refresh guidance. Core/JS checks pass; visual acceptance pending. Installed in owner-authorized 0.22.1 update; missing-device visual/focus acceptance remains pending.

Rehearsal selection follow-up (RH-FR-009–011, RH-NFR-004): local implementation adds explicit eligible-device selection, collapsed exclusions and actionable Apply prerequisites. Included in 0.22.1; hardware acceptance remains owner-supervised.

CF-FR-008–009 / CF-NFR-004: remembered-power policy implemented in 0.22.1 alongside existing captured/current preservation. Explicit mode/temperature editing remains specified for a later implementation.

0.22.1 deployed and read-only verified after one restart: remembered-settings selection works for an Off HVAC target, eligible-device bulk controls and exclusions behave as specified. No test/control run activated; hardware acceptance remains owner-supervised.

0.22.2 / RH-FR-012 and RH-NFR-005: supervised rehearsal removes explanation forms and treats resolved same-device writers as warnings. Scheduled activation safeguards unchanged. Implemented and deployed in 0.22.2; 94 core/70 web and 50 HA rehearsal/execution tests on each supported version pass. Installed read-only powder-room review verified without forms or unrelated automation entries.


## Feature 022 — armable workflow, stage 1
AW-FR-001–004 and applicable AW-NFR-001/002/004 are implemented and locally verified: grouped planner commands, a mobile drawer collapsed by default with per-tab preference, and separate read-only draft/control/observation/climate status. Compact status avoids inventory discovery and reports the next pending control event. This checkpoint is not deployed and changes no saved household observations or activation state. Scheduled control remains lighting-only. Evidence reuse, target-aware unattended conflict review, frozen-draft comparison, qualified scheduled HVAC/fans and unified outcomes remain staged work. See Feature 022 verification and checkpoint 033.


Stage 1 deployed as 0.22.3 after owner authorization: 77 installed files verified, four stores unchanged during installation, on-host backup and one HA restart. Installed planner shows the same scheduled observation and no active/pending control. No household settings, observation or activation changed. Later stages remain pending.
