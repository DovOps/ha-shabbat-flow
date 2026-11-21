# Feature 017 — permanent room fan assignments

Status: implemented, tested and deployed; local and live-read verification in checkpoint 026. Owner fan selections remain explicit.

## Functional requirements
- FAN-FR-001: Room setup provides an optional Fans role separate from lights and HVAC. Accept native fan entities and switch-controlled fans; no automatic selection or inferred ownership. Rooms without fans require no configuration.
- FAN-FR-002: Offer an optional configurable HA Fans label binding, matching entity or device labels within the selected room. Existing selections remain visible even after label/area changes. Show-all-room and all-areas overrides remain available. No special label is mandatory.
- FAN-FR-003: Persist fan assignments with household settings and copy them to new dated planner snapshots with semantic fan metadata. Existing saved plans do not change silently. Assignment alone creates no operating window; users select independent fan windows in Activities, fans and comfort.
- FAN-FR-004: Show fan names and HA icons in room summaries. Support rooms with only fan assignments. Retain duplicate-role/room, missing/disabled entity and changed-binding checks. Fans cannot stand in for required bathroom lights.
- FAN-FR-005: Fan windows remain preview/observation-only, independent of HVAC mode, speed and temperature; do not modify speed, oscillation or devices. Existing runtime/resume qualification requirements still apply.

## Nonfunctional requirements
- FAN-NFR-001: Migrate old saved rooms to empty fan arrays without selecting devices or mutating old drafts. Accept legacy payloads and label bindings; reject unknown roles and invalid domains.
- FAN-NFR-002: English/Hebrew labels, guidance, icons and directional layout match the existing wizard. No household names or exceptions in reusable source.
- FAN-NFR-003: Regression-test migration, filtering, exclusive ownership and snapshot propagation; retain deterministic planning and no-device-control behavior. No new dependencies.

## Acceptance
Save an explicitly selected native fan or fan switch in a bedroom, reload setup, create a new plan and select that fan in an independent activity window. A room with no fan stays unchanged. A label filter may narrow candidates but never changes stored assignments.
