# 0.17.0 verification

Planning and shadow-observation implementation, not live-control qualification.

| Requirements | Evidence |
| --- | --- |
| AC-FR-001, NFR-001 | Explicit immutable meal presets; shared HTML/PDF effective end; empty extension preserves original events; original plans continue through unchanged compiler. |
| AC-FR-002–004 | Native demand union, sleep overlap rejection, snapshot-anchor resolution, meal-linked cleanup/away behavior, explicit exclusion without initial Off, multi-day copy remaps meal IDs and preserves offsets. |
| AC-FR-005 | Existing bathroom daylight/night tests retained; additive suitability field and bilingual help; no implicit policy migration. |
| AC-FR-006–010,013 | Strict threshold equality, heating/cooling direction, C/F conversion, hysteresis/dwell, gaps/clock rollback and signal gates; fixed/conditional overlap rejection. HA sampler test verifies initial evidence, missing/recovery evidence, external release and zero actuation. |
| AC-FR-011–012 | Fan track-only test, semantic-role validation, existing ownership diagnostics. Initial/resume declarations are not qualification. |
| AC-FR-014 | Feedback category/note bounds, summary export; no automatic schedule adjustment. |
| AC-NFR-002–006 | EN/HE catalog parity; existing DST, bounded mappings and observation tests; lazy optional signal rendering; no new dependency; repository hygiene. |

Final automated checks: 91 Python core tests, 60 JavaScript tests, 113 HA tests on each of HA 2026.8.2 and 2026.11.2. HA test dependency deprecation warnings remain. Local browser checks cover meal preset selection, new activity setup and English/Hebrew rendering. No hardware control test was performed.

Remaining acceptance: user household mapping review, extended mobile/native PDF review, sensor measurement freshness, manual-hold/ownership/recovery execution contracts and provider-specific native resume. Conditional/fan/appliance control remains unavailable. Shadow samples are counterfactual intent under observed inputs, not a causal prediction of indoor temperature after hypothetical switching.

Authorized HA deployment: 55-file parity, saved-store preservation and live meal-preset preview verified. No plan saved over, study started or device control activated during verification.
