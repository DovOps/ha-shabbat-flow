# Feature Specification: multilingual household preview planner

**Feature Branch**: `001-preview-planner` | **Created**: 2026-11-17
**Status**: Implementation checkpoint; no production activation
**Input**: Reusable Shabbat planning, English/Hebrew parity, room/meal choices, independent HVAC and lighting offsets, fictional examples only.

## User Scenarios & Testing

### US1 — Explain a household plan (P1)
A family selects planned rooms and meals and sees exactly which logical resources change and why.
Independent test: compile the fictional sample without HA or credentials.
Given either room in a shared group is used, the union of configured shared resources appears once. Given nobody is home but a room or home meal is selected, preview is rejected rather than silently clearing intent.

### US2 — Adjust independent timings (P1)
A user edits bedroom pre-conditioning, shared-space HVAC-off and lighting offsets independently.
Independent test: change one slider; only its event class changes. Offsets are elapsed minutes from candle lighting. Sunrise offsets remain explicit. Times retain their local date and UTC instant across midnight/DST. Unsupported multi-day input is rejected.

### US3 — Use Hebrew or English and save a draft (P1)
A user switches language, saves locally, reloads and exports the draft and preview.
Independent test: Hebrew uses RTL, every visible message is translated, and event identity/timing is unchanged by locale. A corrupted or incompatible local draft gives a localized error and is not loaded. Storage failure is reported, not represented as a successful save.

## Requirements

- FR-001: Versioned plan accepts home flag, room use, meal selections, dated timezone-aware calendar anchors and independent timing offsets, including bedroom sleep-light cutoff.
- FR-002: Configuration supplies multilingual room/load names and arbitrary shared dependencies; no occupant names or fixed entity IDs in engine.
- FR-003: Union shared dependencies, deduplicate identical actions, report same-instant contradictory state commands and missing mappings.
- FR-004: Compile candle-lighting-relative evening events, explicit sunrise morning/shutoff events and fixed dated morning events into sorted local/UTC events with rule reasons.
- FR-005: Bedroom HVAC start, shared HVAC stop and lighting changeover are independently configurable. Unsupported or out-of-period timing is rejected.
- FR-006: Reject contradictory nobody-home plans, invalid IDs/types, malformed timestamps, incorrect timezone offsets, wrong anchor order, unsupported language/version and multi-day periods. Return localized error codes without raw input in errors.
- FR-007: Show multilingual form, accessible controls, timeline, reasons and validation; Hebrew is RTL, mixed technical IDs/times isolated LTR. UI language is an explicit preference.
- FR-008: Save/load draft only in the current browser on explicit click; reset/delete and export are explicit. Never auto-upload. Export warns that user-entered details may be private.
- FR-009: No Home Assistant client, credentials, service calls, activation endpoint or production configuration changes exist in this increment.
- FR-011: Each room defines a homeowner-selected sleep_lights list (possibly empty). For used rooms only, preview an idempotent off at a separate adjustable candle-lighting offset. Do not turn these lights on first, infer current state, or switch off shared dependency loads. This cutoff is independent of HVAC and shared-space lighting.
- FR-012: Display the approved original turquoise candle-and-ribbon logo from a local asset in the responsive dashboard header; no remote asset requests.
- FR-010: Clearly mark samples and supplied calendar times as illustrative, not automatically computed zmanim or live household status.

### Nonfunctional requirements
- NFR-001: Compiler output is identical for identical inputs; event ordering and content digest are locale-independent.
- NFR-002: Zero third-party runtime dependencies, remote fonts, telemetry or external requests for the local preview.
- NFR-003: EN/HE key parity; all runtime validation codes and rule labels covered; language switch preserves data and focus. At 375px viewport no page-level horizontal overflow; all controls have labels and are keyboard reachable.
- NFR-004: Validate bounded requests (128 KiB, 100 rooms/loads/dependencies) and reject unknown fields. Server binds loopback only and rejects cross-origin/mismatched Host requests. Render user-provided labels as text, never HTML.
- NFR-005: Fictional configuration only in tracked files, no absolute local paths/credentials/household exports. Git ignores private runtime files; a repository hygiene check runs in CI. This is defense in depth, not a guarantee against all PII.
- NFR-006: Standard sample compiles in under 250ms per run on the documented local test host; test 100 iterations. No network in compiler.

### Key entities
House configuration; room; load; shared dependency; plan; dated calendar snapshot; event; validation issue; preview digest. See data-model.md.

## Success Criteria
SC-001: All functional requirements link to checks in analysis.md and pass before the checkpoint.
SC-002: A nontechnical user can change sample rooms/meals and see a multilingual preview locally without an HA account.
SC-003: No production-write path exists; source inspection and transport tests verify the boundary.

## Assumptions and limits
This is an ordinary single-Shabbat sample preview, not a deployable schedule. Supplied dates must be a Friday and Saturday, and end within Saturday. No calendar calculation or entity registry connection yet. No temperature control, midday naps, automatic feedback, automation suspension or outdoor extension execution. These remain in roadmap.md, not silently omitted product requirements. Generic dependencies are configurable through the example JSON; a visual mapping editor is later work. Use display-neutral fictional rooms. The public license remains undecided.
