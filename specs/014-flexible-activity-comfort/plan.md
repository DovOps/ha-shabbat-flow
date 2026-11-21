# Implementation plan

Status: planning and shadow stages implemented in 0.17.0; live qualification remains pending. Reuse generic groups, dated room uses, demand union, shared report renderers and feature 010 ownership/observation infrastructure. No new dependency proposed.

1. Add additive models and EN/HE wizard controls for meal duration/cleanup, multiple recreation/playtime windows, subgroup phase participation, optional service schedules and bathroom daylight suitability. Preserve existing schedules until edited. Test compiler unions, sleep conflicts, midnight/DST and multi-day behavior.
2. Add independent fan/outlet mappings and preview lanes with explicit semantic load type and execution eligibility. Keep appliance execution excluded from first live rollout; verify hardware separately.
3. Add per-period room comfort choices and explicit comparison target/mode/sensor contracts. Implement deterministic temperature-policy replay and shadow decisions first, including hysteresis/dwell/unknown handling. Freeze policy inputs and distinguish eligibility windows from predicted On states in HTML/PDF.
4. Extend feedback classifications and comparisons to separate intentional new behavior and exceptional weekends from mismatch. Record comfort reports without inventing occupancy or fan state evidence.
5. Qualify fixed lighting and HVAC execution under feature 010 independently of these broader enhancements. Resolve ownership, initial state, device resume and recovery before arming any subset. Conditional HVAC/fans/appliances each require separately tested adapters and acceptance; no all-or-nothing activation.

Verification: fictional unit/integration tests mapped to AC-FR/NFR, bilingual browser/mobile/print checks, same-input replay, adverse sensor/restart/manual-override tests. Production installation and control tests are separately authorized and recorded. An observation-era final trial is not proof that a live executor is ready.

Implementation: pure extension compiler, lazy activity-signal picker, shared effective meal times in HTML/PDF, bounded HA comfort sampler. See verification.md for evidence and limits.
