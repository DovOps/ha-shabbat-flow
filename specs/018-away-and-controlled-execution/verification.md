# Verification — 0.20.0

GO-FR-001: JS away/return-home/legacy draft/multiday tests and core away completeness tests; fictional browser selection hides meal controls and marks Away while retaining explicit conflicting room choices.

GO-FR-002–009 / GO-NFR-001,003: `tests/ha/test_execution.py` covers approval/arm idempotency, persistence reload, exact service payload, already-correct no-op, linked observation/export, source/mapping/storage/unavailable/missed/disarmed blocking, known reactive writer, unknown-source attestation, entirely-away refusal, admin permissions and strict API fields, crash-intent boot wait, bounded corrections and user override, overlap, in-flight disarm, stale revision/deadline, and unattributed matching state excluded from recovery ownership. Both-language control-report PDF generation tested. Production services are never used in tests.

GO-NFR-002: English/Hebrew catalogs have matching keys. Fictional browser review verified directional checkbox layout and separate qualification/exclusion gates. Home activity cards distinguish control from observation; HTML/PDF/JSON reports include an execution ledger and avoid no-command claims on controlled runs. Source identity and actor attribution stay private; no real household fixture is included.

GO-NFR-004: one-second timer, four concurrent calls, ten-second service deadline, thirty-second confirmation, 120-second grace, two corrections maximum, bounded stores, summary polling without full ledgers. These are enforced limits, not production latency measurements. Automatic retry, full external handoffs, runtime failure push alerts and qualified native HVAC/fan/appliance execution remain open.

Regression: 92 core tests, 66 JavaScript tests, 140 HA tests on each supported runtime (2026.8.2 / 2026.11.2). Repository hygiene and versioned ZIP verification; website both locales checked. Installation and actual device acceptance are separate: see checkpoint-027 for installation evidence. No production run was approved or armed during development.
