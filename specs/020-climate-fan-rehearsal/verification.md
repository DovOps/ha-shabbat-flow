# Verification
- CF-FR-001: JS duration clipping test keeps source/defaults unchanged; existing clock/DST invalid-window cases remain rejected. Adjacent accessible feedback and focus implemented in nap UI.
- CF-FR-002–006 / CF-NFR-001–002: `test_rehearsal_climate.py` uses HA types and service spies for climate/fan/switch On, Off, no-op and restore; baseline capture, expiry, identity, missing mode/temperature, settings drift, temperature reset, capture invalidation, fan preset and climate writer discovery. Existing rehearsal/lighting isolation tests remain.
- CF-FR-007 / CF-NFR-003: EN/HE parity, distinct capture/apply labels, reviewed settings and private contracts/observed settings in JSON.

Deployment/visual evidence pending. Hardware acceptance remains owner-supervised; no real device calls in development tests.

Automated checks: 169 HA tests on both 2026.8.2 and 2026.11.2, 94 core and 68 JavaScript tests pass. Generated assets, hygiene and whitespace checks pass. Both website locales build; link checks pass. Fictional EN/HE nap creation, boundary explanation and editable times visually verified. Package SHA-256: `9d829b80997de6544c96922be3860a601d5e977c582e52bcfc8a01bf6120eac2`.
