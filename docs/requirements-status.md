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
