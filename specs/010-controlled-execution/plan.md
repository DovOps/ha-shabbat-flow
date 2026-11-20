# Feature 010 implementation plan

Status: defaults accepted; observe-only checkpoint implemented below. Live execution remains deferred. No production changes in this checkpoint.

## Technical context

Target: existing custom HA integration on the two tested HA versions (2026.8.2 / 2026.11.2), Python supplied by HA; pure compiler retains its Python 3.11+ baseline. Frontend: existing JavaScript modules and EN/HE catalogs. Tests: unittest, Node test runner and isolated HA pytest harness. Proposed storage: HA Store with serialized awaited persistence, subject to E002 validation. Scale/performance and limits are EX-NFR-005–007. No new package or borrowed design.

## Architecture proposal

Keep the pure compiler unchanged as the authority for normalized intentions. Add a separate HA-native execution boundary; preview routes and the standalone development server cannot access actuator services. No third-party scheduler or new runtime dependency proposed. Reuse authenticated HA integration infrastructure and standard HA storage/event/service facilities after compatibility validation. Review the proposal before introducing an executor under docs/dependencies.md.

Proposed modules (names are design, not existing files):
- `execution/models.py`: immutable approved snapshot, run/resource lifecycle, typed commands and versioned ledger records.
- `execution/repository.py`: awaited persistence, serialized compare-and-set transitions, revision/idempotency checks, bounded retention and migration.
- `execution/ownership.py`: canonical physical-load reservations, read-only automation source report and action-interval handoffs.
- `execution/adapters.py`: exact target allowlist, binary-lighting adapter and explicitly registered/verified HVAC native-resume adapters. No generic arbitrary-service escape hatch.
- `execution/runner.py`: UTC scheduler, per-load serialization, dispatch ledger, bounded concurrency/retries and startup reconciliation.
- `execution/observations.py`: fresh state confirmation, context-aware diagnostics and settings drift detection; no continuous state-enforcement loop.
- Existing authenticated backend and multilingual panel: approval review, separate arm/disarm, run status and observed-versus-planned export. No browser-token forwarding into the inner application.

## Persisted contract

Keep household mapping storage separate from execution storage. Use one versioned execution envelope with serialized awaited saves for cross-record reservations/run transitions; validate HA Store guarantees and power-loss behavior in a spike. If those guarantees do not meet fault-injection tests, stop and propose an alternative rather than claiming transactional durability. Suggested records:

- ApprovedPlan: revision/digest, schema/compiler version, exact normalized input/events, calendar snapshot, target mappings, adapter fingerprints, policy, exclusions, approver/time.
- Run: run ID, approved digest, lifecycle, activation actor/time, first action, final expiry, ownership epoch, per-resource status, idempotency key.
- EventAttempt: stable event ID, due UTC, attempt number, pre-call state, dispatch-intent/ack/observation timestamps, result, uncertainty, error code.
- Ownership: physical resource, owner and [start,end) interval, source hashes, handoff event/time; exact final boundary commands explicitly represented.
- HVACBaseline: resource/adapter identity, retained settings with provenance and observation freshness, recorded-before-Off timestamp and qualification record.

Do not store credentials. Include export/schema version and correction records; never rewrite the approved evidence. Terminal-run evidence pruning must not delete active recovery keys. Corrupt or failed persistence stops dispatch.

## Lifecycle and race handling

Draft -> Approved -> Armed -> Running -> Completed. Approved/Armed/Running can be Disarmed; failed integrity blocks the run. Per-resource Blocked can coexist with Running/degraded status for independent resources. Blocked does not auto-resume. Review UI explains that a failure is not an all-Off command. Approval and arming persist atomically with revision checks; arming has no immediate device effect.

A callback checks run revision/ownership, persists attempt intent, then rechecks cancellation immediately before dispatch. Disarm serializes against dispatch-start and cancels timers/retries. Acknowledgement is distinct from matching fresh state. Crash ambiguity cannot be eliminated across a physical call: reconcile by observation and adapter repeat-safety under the grace policy. Persistent event IDs prevent ordinary duplicate replay; no physical exactly-once claim.

On restart: load -> validate schemas/digests/adapter contracts -> rebuild reservations -> wait bounded readiness -> inspect uncertain/past-due events -> satisfy/skip/block under approved policy -> register future callbacks. Never queue all missed historical actions. External-release handoffs and expiry terminate planner recovery ownership.

## Delivery slices and dependencies

| Slice | Deliverable | Gate / verification |
|---|---|---|
| E0 | Review policy, exact API/source capabilities and provider qualification approach | Owner review of Feature 010 and native executor proposal; no device calls |
| E1 | Pure models, durable repository, approval/arming state machine with fake clock/adapters | Authorization, race, persistence-failure and no-actuation tests |
| E2 | Read-only automation forecast/conflict report and physical-load ownership | MD-FR-020–022 plus unresolved/changed-source/handoff tests; blocks must be honest about incomplete discovery |
| E3 | Shadow runner and restart ledger, zero-action adapter | Simulate all lifecycle/fault paths; restart during every attempt boundary; snapshot/digest unchanged |
| E4 | Allowlisted lighting adapter and local execution status | Explicit weekday pilot authorization; binary pair/access-light tests; cancellation and outage tests |
| E5 | Qualified HVAC native-resume adapter and per-unit tests | No generic fallback; settings preservation, off-baseline, drift and cycle constraints verified |
| E6 | EN/HE approval/arm/disarm and review UX, exports, retention | Accessibility/RTL/mobile checks, no hidden unsupported/excluded loads; all criteria traceable |
| E7 | Packaging, migration/rollback and limited live pilot | Compatibility suites, approved exact plan and allowlist, explicit arming, reviewed fallback |

E1–E3 can progress without production actuation. E4/E5 remain disabled until their adapter and weekday test gates pass. E6 status/preview UX can develop alongside E1–E3; activation controls stay unavailable until validation is complete. A successful shadow weekend informs schedule defaults but cannot qualify actuator/recovery reliability.

## Test strategy

Pure fixture tests cover rules, limits and deterministic IDs; fake-clock tests cover grace, deadlines, DST, expiry, multiday, handoffs and clock jumps. HA harness tests on both supported versions spy on all service calls, permissions and exact payloads. Fault injection covers save failure, crash before/after send, uncertain acknowledgement, duplicate callback/request, competing plans, disarm races, source changes and unavailable entities. Stress reference hardware and workload are recorded alongside lateness percentiles. End-to-end EN/HE review tests verify included/excluded devices, readable reasons and keyboard/RTL use. Live weekday tests require separate authorization and publish only generic findings, never household data.

## Rollout and rollback

Keep preview usable while execution is disabled. Install does not arm. Preserve previous package and execution/household stores; schema compatibility must be checked before resume after upgrade or downgrade. Disarm before planned rollback and verify no pending callbacks; if a run is armed, UI must describe disruption. Restoring storage cannot recall a dispatched physical command. No automatic restoration of prior device states, boiler rules or whole-house settings. Initial scope excludes automation mutations, reducing rollback to stopped future actions and explicit manual review.

## Current review result

Constitution satisfied by separation of preview, immutable approval, named ownership, explicit activation, multilingual requirements and household-data exclusion. No third-party designs/packages selected. Main risks: incomplete automation introspection; provider-specific HVAC semantics; nontransactional physical commands; availability during HA outage. Each has an explicit blocking/uncertain outcome, not a fabricated guarantee. Native provider/source APIs and persistence guarantees need an implementation spike; this plan is not a claim those risks are already resolved.

## Observe-only checkpoint implementation (0.12.0)

The accepted defaults remain future live policy. This checkpoint implements a separately named `observe` lifecycle (scheduled/observing/completed/stopped), not approval or arming. `observe.py` owns immutable plan snapshots, server recompilation, idempotent start/overlap rejection, sampled event ledger, restart gaps, settings/power comparisons, report-only recovery checks and export. It contains no device service caller. `ownership.py` implements conservative interval-overlap diagnostics and a bounded read-only forecast; it grants no live clearance.

Storage spike result: the tested HA Store implementations can log and consume write failures. Instead, observation uses a dedicated schema/checksum envelope in `.storage`, written with temp-file fsync, atomic replace and directory fsync via the executor. Errors propagate and prevent in-memory publication; an error disables further collection until reload. This is not a transaction with a device and does not qualify live execution durability. The filename remains separate from household settings. Store corruption never resets an existing file to an empty run list.

Forecast scope: enabled direct light/switch/climate On/Off sequences, bounded literal delays, daily literal clock triggers, weekday-only conditions and sunrise/sunset offsets via HA's existing sun helper/location. The preparation day is included. Config/timezone/sun-source fingerprints accompany forecasts. Unsupported templates, helper times, state/issur conditions and triggers, arbitrary scripts, dynamic area/label targets or other actions stay unresolved. Complete MD-FR-020–022 coverage and live ownership/handoffs remain open. No other integration is installed and no calendar settings are changed.

Observe snapshots may start late with explicit unknown prior coverage. One-minute sample intervals are estimates; restart or >90-second gaps are unknown. The ledger reports a sampled comparison or missed/superseded observation, never a successful device dispatch. HVAC power agreement and settings comparison have separate totals; an unavailable initial preserve-settings baseline stays unknown. Reconciliation knobs control reporting only; future corrections and persistent correction budgets are specified but not implemented.

No HA installation or production observation started at this checkpoint. EN/HE controls, interleaved unmanaged event rows and inherited PDF output are implemented; full interactive/browser and PDF pagination QA remain pending. Live activation/retry/reconciliation implementations, provider qualification, state-condition forecast and full target expansion remain unchecked tasks.

### Forecast compatibility patch (0.12.1)
Accept editor metadata and resolve literal label/area/device selectors using HA’s existing read-only target helper. Filter to service domain, reject missing/empty selectors, and fingerprint resolved membership. No service invocation or new dependency. State/issur conditions, scripts and template targets remain unresolved. Test native registry expansion on both supported versions before deployment.

### Hourly thermal evidence
Add a read-only `thermal.py` collector using already accepted HA state/registry APIs. Freeze all enabled climate identities and selected weather source independently of commanded-load mappings. Keep measured temperature out of preserve-settings comparison. Use UTC hourly slots from preparation start (local labels in exports), with missing-slot markers and actual collection timestamps. Extend observe export and source selection/summary in both languages; no actuator or new dependency. Backward-compatible active-run enrichment starts at upgrade, with explicit unknown past coverage.
Thermal visualization: add a pure chart model and native SVG per-room charts, hourly mode markers and accessible data tables. Observation print is a separate selected-run report with original logo, frozen period and digest; it must not borrow events from an edited preview. No chart library or new dependency.

Summary report follow-up: reuse the run’s sampled comparison totals in the printable report alongside thermal coverage. A self-contained fictional example is generated from the actual report renderer, not a separate mockup that could imply unimplemented analysis.
