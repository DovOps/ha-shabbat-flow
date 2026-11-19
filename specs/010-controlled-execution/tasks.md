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
