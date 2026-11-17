# Feature 007 — HA-synchronized household setup

## User decision and scope
Use the installed HA registries as the live inventory, without a manual import. Keep household intent separately in this installation. Implement and deploy a preview upgrade under the user's explicit authorization. No device execution or existing-automation edits.

## Functional requirements
- SYNC-FR-001: Discover floors, areas, devices and registered relevant entities through HA registry helpers. Resolve area as entity override, otherwise device area. Show unassigned entities. Never infer room purpose from names or state.
- SYNC-FR-002: Return current registry/state values on every inventory request; refresh the visible setup within 30 seconds while connected and on focus. Display last successful refresh and connection failures. Manual refresh is available. No repeated household export/import.
- SYNC-FR-003: Admin setup supports excluding/including areas, sleeping/recreation purposes independently, main/night lighting and HVAC roles, explicit shared-area dependencies, and explicit HVAC mode/temperature/fan/lead time. Suggest only candidates; additions never become mapped automatically.
- SYNC-FR-004: Store reviewed mapping references by stable entity-registry ID and area ID using HA Store, with schema and revision. Names and entity IDs resolve live after rename. Device moves, deleted areas/entities, disabled entities, unavailable states and capability changes are visible; never choose replacements automatically. Re-save explicitly acknowledges structural changes. Removed references remain visible until corrected.
- SYNC-FR-005: Preserve unsaved setup edits during refresh and prevent concurrent lost updates with settings revision plus structural-inventory digest. Save only when validation succeeds, persist before acknowledging success, retain old data on failure.
- SYNC-FR-006: Generate a new planner workspace from the saved household and explicitly supplied dated anchors. Use actual room/load labels and stable internal IDs; shared loads retain a single physical identity. Room-use and meal choices start unselected. Do not fabricate future sunrise/holiday coverage. The initial date form supplies one segment; the existing advanced planner supports reviewing up to three segments.
- SYNC-FR-007: Existing browser workspaces remain unchanged when inventory/settings change. Show that they are snapshots. New workspace generation refuses unresolved mappings. No approved-plan execution exists in this release; future execution MUST freeze dated plans, bindings and rules, and define missing-device behavior.
- SYNC-FR-008: Ship EN/HE UI, RTL, keyboard-operable labelled native controls. Treat homeowner names as data, not translated product text. Keep standalone fictional demo available separately; installed entry point opens real household setup.

- SYNC-FR-009: Opening a planner must show actionable validation beside the initiating button, including missing calendar fields, observance choice, unsaved setup and missing planning roles. Show progress, reject duplicate submissions and preserve form inputs on failure.

## Nonfunctional requirements
- SYNC-NFR-001: Admin/auth guards on read/write APIs; bounded JSON inputs; no tokens, unique hardware identifiers, arbitrary entity attributes or histories in inventory responses. No household data, screenshots or exports in repository examples/tests.
- SYNC-NFR-002: Writes confined to ShabbatFlow storage. No device/service calls, registry mutations, recorder changes or existing-automation changes. Poll only while setup is visible; no server polling scheduler. Limit configuration to 20 enabled planning areas and 100 mapped loads to stay within compiler bounds, with explicit errors rather than truncation.
- SYNC-NFR-003: Deterministic configuration and workspace generation from inventory/settings/calendar snapshots; stable load identity and fail-closed validation for unsafe or unsupported HVAC capabilities. Unknown capability values are not guessed.
- SYNC-NFR-004: Test registry rename/move/delete/add, inherited area, unavailable state, persistence/reload, stale writes, admin/body bounds, shared-load deduplication, locale parity and personalized compilation with synthetic fixtures. Verify against HA 2026.8.2 and 2026.11.2.
- SYNC-NFR-005: Version static asset URLs as a complete asset tree so HA/browser caching cannot mix releases. Upgrade with recoverable copy of the prior integration, restart and normal config-entry reload; verify installed UI, calendar and sample preview without controlling devices.

- SYNC-NFR-006: Planner feedback is localized, keyboard-focusable and announced through a live region. Test invalid inputs, server failure, storage failure and successful navigation without device calls.

## Deferred
Invented planning areas independent of HA areas, automatic future multi-day calendar acquisition, automation import/replacement, shared weekly-plan storage, family non-admin access, activation/execution, feedback storage and MCP remain separate features. Inventory sync is bounded polling while the page is open, not a claim of push-based instantaneous updates.
