# Specification consistency review

Documentation-only checkpoint; no executor files changed and no HA deployment performed.

Coverage: EX-FR-001–008 cover lifecycle/activation, 009–014 existing automation ownership, 015–020 HVAC preservation, 021–029 dispatch/recovery/outcomes. EX-NFR-001–012 provide measurable boundaries. Acceptance cases A1–A12 and tasks E001–E012 link the requirements to future verification.

Clarifications relative to earlier roadmap: automatic suspension is deferred, not deleted; explicit-profile HVAC remains a preview capability but is outside the first executor; existing morning-release selection needs a verified ownership handoff before execution; expiry is not an invented all-Off; the live observance sensor does not override frozen timestamps. A stale/unknown baseline blocks the affected resource, not an uncontrolled replay of missed actions.

Remaining design evidence: supported automation-source discovery coverage, persistence durability under HA shutdown/power interruption, exact device adapters and quantitative performance on reference hardware. E002 resolves these before implementation promises are made. Review decisions remain in spec.md; no unresolved policy is presented as approved.

Validation performed for this checkpoint: 76 existing Python tests and 39 existing Node tests passed; repository hygiene and diff whitespace checks passed. These establish no regression from this documentation change, not execution behavior. No Feature 010 acceptance tests or real-device pilot have run because execution is not implemented.

## Observe-only implementation checkpoint
The specification-only statement above describes the preceding checkpoint. Version 0.12.0 implements the bounded observe milestone documented in plan.md and docs/checkpoint-012.md. Live arming, actuation and corrections remain absent. Acceptance scenarios for live dispatch remain untested; observe-specific fault/coverage tests passed. Full automation-condition/target expansion remains explicitly incomplete.
