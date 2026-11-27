# Verification
- CF-FR-001: JS duration clipping test keeps source/defaults unchanged; existing clock/DST invalid-window cases remain rejected. Adjacent accessible feedback and focus implemented in nap UI.
- CF-FR-002–006 / CF-NFR-001–002: `test_rehearsal_climate.py` uses HA types and service spies for climate/fan/switch On, Off, no-op and restore; baseline capture, expiry, identity, missing mode/temperature, settings drift, temperature reset, capture invalidation, fan preset and climate writer discovery. Existing rehearsal/lighting isolation tests remain.
- CF-FR-007 / CF-NFR-003: EN/HE parity, distinct capture/apply labels, reviewed settings and private contracts/observed settings in JSON.

0.22.0 deployed with 72 files byte-verified, saved stores preserved and one restart. Installed nap creation/clipping and HVAC review/baseline blocker verified without saving test draft edits or changing devices. Fictional EN/HE visuals verified. Hardware acceptance remains owner-supervised; no real device calls in development tests.

Automated checks: 169 HA tests on both 2026.8.2 and 2026.11.2, 94 core and 68 JavaScript tests pass. Generated assets, hygiene and whitespace checks pass. Both website locales build; link checks pass. Fictional EN/HE nap creation, boundary explanation and editable times visually verified. Package SHA-256: `9d829b80997de6544c96922be3860a601d5e977c582e52bcfc8a01bf6120eac2`.

0.22.1 follow-up: 32 focused rehearsal tests pass on HA 2026.8.2 and 2026.11.2; 94 core and 70 web tests pass. Native remembered-power service spies verify entity-only arguments, no capture, reported post-settings, policy-change invalidation, absent-service rejection and intervention-safe restore. Package/hygiene checks pass. Installed 76 files byte-verified with integration and three-store backups; stores unchanged during installation. Backend restart completed; installed EN/HE policy labels and native remembered review verified without actuation. No rehearsal applied by deployment.

Additional startup/API regression: 88 integration tests pass on HA 2026.11.2.
