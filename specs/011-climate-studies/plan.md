# Implementation plan
Extend the existing observer with an explicit climate_study kind and validated immutable study bundle. Keep shared persistence, minute ticks, hourly thermal snapshots and export; bypass schedule compilation, ownership forecasts and recovery checks for studies. Add optional reference sampling and read-only registry candidates. A separate page exposes zone/light/reference selection and report controls, linked from setup. Reuse report renderer with study-specific headings and observed-only bands. No runtime dependency or actuation adapter.

Verify API validation, idempotency, stop/completion, restart, missing references, no service calls and legacy regression on both supported HA versions. Package as 0.14.0. Installation requires separate authorization; production remains 0.13.0 until deployed.

Room-activity follow-up: reuse existing light/switch registry selection and minute sampling. Broaden setup copy to room activity signals, freeze per-load signal kind, and label observed switch bands separately from light bands. Preserve existing wire keys and infer domain for legacy report records only. Verify device-area inheritance, non-light switches, On/Off changes, gaps and report labels.

0.14.1 bulk-selection follow-up: room-scoped native buttons update selection and checkbox state in place. Do not redraw observation controls or include collapsed other-area choices. No backend changes; existing input bounds remain. Installed version remains 0.14.0 until authorized upgrade.

0.16.2: Update zone bodies in place, defer cross-room lists until disclosure, paginate by 50 and preserve observer controls. Verify against a 100-zone/2,000-signal fictional fixture and DOM regression tests.

0.16.3: Keep automatic native climate sampling unchanged; clarify the default and optional independent comparison in EN/HE. Preserve observer selector state across locale redraws. Extend large-inventory language regression and verify built-in measured versus target temperature while Off with no reference.
