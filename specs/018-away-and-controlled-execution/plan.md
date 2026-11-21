# Plan
1. Normalize away meal UX and compiler completeness without changing stored observations.
2. Implement independent private execution store, review/approval/arm/disarm lifecycle and conservative source/target checks.
3. Add explicit binary adapter with state-aware dispatch, durable ledger, confirmation and bounded restart/reconciliation.
4. Connect observation/report exports and EN/HE review/status UI; retain unsupported devices as exclusions.
5. Verify fake-time/fault/concurrency/permission tests, both HA versions and browser flow; deploy unarmed and publish release evidence.
