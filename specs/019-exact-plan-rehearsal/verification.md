# Verification

- RH-FR-001–003: `tests/test_rehearsal.py` covers exact compiled instants, last-known state projection, untouched unknown states, scope validation and candle anchors without rewritten dates.
- RH-FR-004–007 / RH-NFR-001,003: `tests/ha/test_rehearsal.py` uses real HA types with service spies: review makes no calls; explicit apply and reviewed restore; idempotency; unchanged source plan and execution/observation ledgers; manual intervention; matching-state no-op; active observance; unavailable target/stale review; persistence failure; expiry; confirmation; restart invalidation/interruption; stop; overlapping control; mapping/source/context drift; admin enforcement and exclusions. Existing executor tests cover binary qualification and dispatch boundaries.
- RH-FR-008: persisted reload, JSON export and feedback assertions. Retention bounded to 20 records/90 days and active batches never pruned.
- RH-NFR-002: English/Hebrew key parity automated; browser visual/keyboard acceptance remains pending because local browser access is unavailable in this session. The fictional loopback gallery serves simulation only and rejects physical application.

Automated checkpoint: 94 core, 67 JavaScript, 154 HA tests on HA 2026.11.2 and 2026.8.2. Generated package, hygiene and website checks recorded in checkpoint 028. No real device tests or weekend arming were performed. Deployment remains pending access to the installed HA host.
