# Feature 006: installable preview sample

Scope: package the existing planner as a manual-install Home Assistant custom integration and sidebar panel. This is an installable evaluation sample, not an executor. User requested deferring further product requirements to the next iteration.

## Requirements
- INSTALL-FR-001: Provide a self-contained versioned ZIP with `custom_components/shabbat_flow`, config flow, EN/HE setup strings, panel, compiler and synthetic examples. No dependency on a development checkout or running loopback server.
- INSTALL-FR-002: Setup/removal through HA config entries. Single instance; admin-only sample panel and authenticated admin-only API. Unloading removes the panel and rejects further application API requests; registered static assets may remain until restart.
- INSTALL-FR-003: No service calls, entity writes, automation/config mutations, recorder access, execution endpoints or background schedule tasks. Installing creates only the integration's own config entry/panel. Browser drafts remain explicit and private to the browser origin; nothing is automatically uploaded to the repository.
- INSTALL-FR-004: Optional owner-selected existing calendar timestamp entities and an active-observance binary sensor. Read only selected state values, preserve unavailable/unknown, include source IDs/update times and HA timezone. No mandatory calendar integration and no inference of provider from entity names. State timestamps must be offset aware; ambiguous/naive values are unresolved.
- INSTALL-FR-005: Show installed-calendar values as an optional source and permit explicit manual overrides using date/time controls in the configured IANA timezone. No raw UTC text required for normal timestamp editing. Reject nonexistent local times and require explicit choice between ambiguous offsets. Preserve second precision.
- INSTALL-FR-006: A current binary signal or one set of upcoming timestamps is not full future calendar coverage. Imported anchors require user review and complete-period validation; do not silently repeat them across multiple days or manufacture holiday boundaries. Complete provider-specific future-date adapters remain next-iteration work.
- INSTALL-NFR-001: Reuse the same compiler/frontend sources through a deterministic build, with a drift check and bounded authenticated preview requests. Do not bundle development credentials, household files, logs or test environments.
- INSTALL-NFR-002: Verify config flow, setup/unload, static registration, authorization, preview parity and unavailable calendar data against a real installed HA package in an isolated environment. State exact tested version; do not claim household deployment or browser/Companion verification without evidence.

## Dependencies and boundaries
HA built-ins only: frontend, http and panel_custom; libraries already supplied by HA. No third-party integration source/design copied. Building and local testing are authorized; installing into the household HA instance is a separate action. Feedback storage, MCP, real-device mapping/execution, HACS distribution and full multi-day calendar acquisition are deferred.

## Preferred calendar provider decision
The user identified the built-in Jewish Calendar integration (`jewish_calendar`) as the default. Entity-registry discovery targets its candle-lighting, Havdalah, sunrise and active-observance signals, verified against HA 2026.11.2 source. The live installation/version has not been inspected in this session. Optional startup ordering permits manual fallback when the provider is absent. This initial adapter reads current selected values only; full future-date coverage remains deferred.

## Release asset identity
- INSTALL-NFR-001: Package validation must reject a mismatch between manifest version, frontend VERSION and versioned static path. HA lifecycle tests must compare the registered module URL to the manifest, not a separately hardcoded version. An installed release is verified through its live versioned assets and actual rendering.
