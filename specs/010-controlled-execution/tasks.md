# Feature 010 tasks

Observe-only milestone is implemented below. The broader live-execution tasks remain incomplete; unchecked tasks are not authorized production actions.

- [x] E000 Draft user stories, FR/NFR, acceptance cases, implementation proposal and review checklist.
- [x] E001 Review numerical policies, native HA execution boundary and no-suspension scope (pilot allowlist remains deferred); (EX-FR-001–020).
- [ ] E002 Spike supported automation introspection, durable Store behavior and provider-native HVAC resume semantics; record exact versions and limitations (EX-FR-009,015–018,023; EX-NFR-004,009).
- [ ] E003 Implement versioned snapshots, ledger, reservations and lifecycle with authenticated revision/idempotency checks (EX-FR-001–008,021–023; EX-NFR-001–004).
- [ ] E004 Implement read-only overlay and scoped ownership review/handoffs, source invalidation and unknown coverage (EX-FR-009–014,022; MD-FR-020–022).
- [ ] E005 Implement fake-clock/shadow dispatcher, state observations, grace/retry rules and restart recovery without actuation (EX-FR-019–029; EX-NFR-003–008).
- [ ] E006 Implement explicit binary lighting adapter, disabled by default; service-spy and concurrency tests (EX-FR-021–022; EX-NFR-001–007).
- [ ] E007 Implement only qualified native-resume HVAC adapters, baseline persistence and drift/cycle tests (EX-FR-015–020; EX-NFR-009,012).
- [ ] E008 Implement EN/HE approval, arming, disarm, exclusions, diagnostics and outcome export (EX-FR-001–008,029; EX-NFR-002,010–011).
- [ ] E009 Verify retention, migrations, restart/downgrade refusal and workload timing limits (EX-NFR-004–009,011).
- [ ] E010 Run complete automated and manual accessibility/RTL suites; map results to acceptance A1–A12 (EX-NFR-012).
- [ ] E011 Obtain explicit weekday device-test authorization; verify each pilot unit, recovery and disarm; keep household evidence outside repo.
- [ ] E012 Package reviewed release with execution disabled; separately authorize deployment, reviewed allowlist and exact plan activation. Do not equate package deployment with arming.

## Observe-only milestone
- [x] O001 Record accepted defaults and add observe/export/reconciliation FR and NFR.
- [x] O002 Inspect storage and automation source APIs on both supported HA versions; implement error-reporting atomic observation storage with integrity validation.
- [x] O003 Implement immutable server-compiled snapshots, idempotent observation start, overlap rejection, retention and stop/configure/export endpoints with admin authorization.
- [x] O004 Implement bounded direct time/sun/weekday unmanaged forecasts, source fingerprints and conservative interval conflict diagnostics; unresolved cases explicit.
- [x] O005 Implement sampled runner, event ledger, unknown restart gaps, power/settings metrics and report-only boot/interval checks. No actuator exists.
- [x] O006 Implement EN/HE observe controls, combined download, summary table and unmanaged schedule/PDF rows.
- [ ] O007 Finish full live ownership/handoff support and state/issur-conditioned forecasts (E004 remains partial).
- [ ] O008 Implement and qualify live adapters, arming and opt-in state correction with persistent cooldown/budget. No production action authorized here.
- [ ] O009 Authorized HA deployment and real observe-run verification, including interactive UI/PDF review.

- [x] O010 Verify metadata and literal registry-target forecast expansion, membership fingerprints and no-service-call regression (EX-FR-034, EX-NFR-015); deploy patch and verify unmanaged events.

O009 deployment and live preview verification completed in 0.12.1; real observe-run/export and PDF review remain outstanding. No observe run was started during deployment.
- [x] O011 Implement/test hourly thermostat and weather evidence, source selector, legacy-run enrichment, multilingual summary and export (EX-FR-035–037, EX-NFR-016).
- [x] O012 Implement/test hourly thermal charts, accessible tables and isolated observation PDF in EN/HE (EX-FR-038, EX-NFR-017).

- [x] O013 Reconcile requirement/rollout index; include sampled totals in printable report and generate a fictional summary example (EX-FR-039).
- [x] O014 Add all-zone sampled power-duration counters and shared active-first chart/table ranking with coverage-aware combined table (EX-FR-040, EX-NFR-018).
- [x] O015 Add linked planned-use/planned-light/observed-light bands, gap-aware tests and updated fictional visual (EX-FR-041, EX-NFR-019).

O009 rollout follow-up: 0.13.0 installed and live observe/weather controls verified. No run started; real collection/export and PDF acceptance remain open. See checkpoint-013.

## Relevant existing-automation preview
- [x] X041 Filter reactive triggers; retain ownership audit and bounded calendar transition support.
- [x] X042 Friendly grouped existing-automation events, device icons and expandable IDs.
- [x] X043 Collapsed diagnostics and concise PDF summaries.
- [x] X044 Verify forecast, renderer, print and package behavior; production installation separate.

## Partial implementation cross-reference
Feature 018 delivers a separately specified binary-lighting pilot: review/approve/arm/disarm, conservative writer blocking, durable dispatch ledger, context-qualified confirmation, linked observation and optional two-correction recovery. This covers portions of E003–E006/E008/E009; those tasks remain open for full Feature 010 scope (HVAC, handoffs, retry/workload qualification and live acceptance).
