# ShabbatFlow Constitution

Version: 1.1.0 | Ratified: 2026-11-17

## I. Repository hygiene and reusable configuration
Contributors MUST keep real home configuration, family details, credentials and household histories outside the reusable repository. Generalize examples and let installers adapt them privately. This is a contribution/data-separation rule, not the product’s headline purpose. No identifying data or embedded credentials in sample assets. Explicit exports explain their contents.

## II. Deterministic local planning
The same normalized plan, mapping, dated calendar snapshot and rules version MUST yield the same events and digest. AI can propose configuration; it cannot execute a plan or change a frozen plan. No network is needed for the fixture-based preview.

## III. Reviewed device ownership
Preview MUST have no device-control path. Separately armed execution requires a named actuator/owner per physical load, an approved immutable plan, explicit activation and tested rollback/recovery. Existing automations are preserved unless their changes are individually authorized.

## IV. Multilingual architecture with English and Hebrew defaults
Use extensible language catalogs and language-direction metadata. English and Hebrew are supported by default. All user journeys MUST work in both default languages, including validation, reasons, onboarding, feedback and errors. Hebrew uses RTL; IDs and timestamps remain readable in bidirectional text. Language changes never change schedule semantics. Missing keys fail tests.

## V. Requirements and evidence
Maintain functional and measurable nonfunctional requirements, explicit deferred scope, acceptance scenarios and requirement-to-test traceability. Test the compiler, edge conditions, privacy boundaries and user-facing workflows. Historical correlation is not occupancy or causality.

## VI. Small reusable increments
Separate logical household configuration from engine and adapters. Reuse existing calendar/timer systems when compatible. Keep speculative integrations behind documented decisions. A local preview is not represented as a production HA integration.

## Governance
Amend this document with an explanation and update affected specs, plans and tests. Unresolved policy must be visible rather than silently invented. User instructions govern approval and commit boundaries.

Amendment 1.1.0: Feature 018 introduces a separate explicitly approved binary-lighting pilot. Preview and observation remain non-actuating; this amendment does not qualify HVAC or authorize any household activation.
