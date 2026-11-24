# Feature 021 — adoption playbook

## Functional requirements
- AP-FR-001: Publish one maintained English/Hebrew adoption guide shared by the HA app and public website: configure, preview, observe, rehearse, restore, limited rollout and review. Explain why weekday preparation matters when correcting a mistake during observance may not be an option.
- AP-FR-002: Provide a labeled Guide navigation entry throughout the app and a contextual rehearsal link. Open help separately so unsaved plan/setup edits survive. Offer section links, language selection and printing without HA API calls.
- AP-FR-003: Distinguish non-actuating preview/simulation/observation, immediate supervised device tests and separately approved scheduled execution. Describe transition versus cumulative state, baseline capture versus pre-test restore, two-minute reviews, inactive-observance requirement, conflicts, no-ops, skipped restore and manual fallback.
- AP-FR-004: Describe explicit fan activity windows and HVAC mode/temperature preservation limits. Current supported scope: supervised qualified HVAC/fan rehearsal and separately approved lighting-only scheduling; no automatic qualification or full-home readiness claim.
- AP-FR-005: Brochure exposes the playbook and rehearsal-led adoption, with readiness gates and links from getting started. Feedback records expected/actual behavior, comfort, failures and settings-versus-product follow-up. Keep personal adoption plans out of public content.

## Nonfunctional requirements
- AP-NFR-001: Read-only, local bundled app help: no device/notification calls, external dependencies, tracking or progress claims. No change to execution eligibility.
- AP-NFR-002: EN/HE parity, RTL, semantic headings, keyboard focus, responsive cards, non-color-only mode distinctions and printable content. Website generated from the same content as the app to avoid divergent instructions.
- AP-NFR-003: Verify locale/schema and deep-link coverage, package parity, repository checks, both website builds and visual EN/HE navigation. Record deployment separately from implementation and supervised hardware acceptance.

## Acceptance
An owner can find the guide from the plan without losing edits, follow one-room rehearsal and restore, and explain what still needs approval before scheduling. A public visitor can find the adoption guide from the brochure. Reading either guide never changes a device or marks a test passed.
