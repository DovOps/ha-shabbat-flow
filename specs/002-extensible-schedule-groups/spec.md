# Feature Specification: homeowner-defined schedule groups

Status: V2 local preview checkpoint: calendar/room-use validation, generic binary/HVAC compiler and opt-in multilingual dashboard implemented. Scene/script adapters, migration and browser verification remain open. The family view now includes day tabs, room tiles and reviewed copy-day. Feature 001 is preserved separately. See plan.md, tasks.md and analysis.md for scope and verification.

## User scenarios
US1: An installer adds a named group such as outdoor access or an additional appliance, selects available targets and previews its dated actions without changing the core engine.
US2: A family includes/excludes a group for the upcoming observance, adjusts approved timing parameters and understands dependencies/conflicts.
US3: An installer maps an existing scene or script rather than replacing working automation. Device-specific modes require explicit capability support.

## Functional requirements
- GR-FR-009: Room usage is a set of time-bounded purposes, not one occupancy checkbox: sleeping, recreation/shared activity, and optional other configured uses. The same room can serve different purposes at different times. Do not infer identity, age or presence from the chosen profile.
- GR-FR-010: Sleeping usage selects Early / Standard / Late or a custom profile. Profiles define independent HVAC pre-conditioning, sleep-light cutoff and wake/off timing adjustments relative to approved anchors. Values are installer-configurable; do not hardcode age-based defaults. Show each profile's resulting local times.
- GR-FR-011: Recreation areas (for example a lower-level lounge or family room) can have usage windows and activity-specific lighting/HVAC independent of sleeping status. When uses overlap or change purpose, show the conflict or explicit precedence rather than silently combining incompatible settings. Preserve the option to leave a room under existing control.
- GR-FR-012: Climate actions cover heating and cooling (HVAC), not cooling-only logic. Validate selected mode, temperature units, target range and fan capabilities against the mapped zone. Seasonal presets remain editable and must not silently switch modes. A preview intention to turn HVAC on is not approval of an inferred mode.
- GR-FR-001: Separate generic groups, eligibility conditions and dated schedule rules from lighting/AC presets. Presets populate this model; they must not define the complete universe of device types.
- GR-FR-002: Each group has a stable ID, localized display names, targets, conditions, owner, desired coverage and independently adjustable timing rules. Support candle-lighting/sunrise offsets and explicit dated wall-clock rules.
- GR-FR-003: Reference existing lights, switches, scenes, scripts and supported typed device actions. Validate required parameters and capabilities. No arbitrary Python, shell, templating or unchecked service execution from imported configuration.
- GR-FR-004: Outdoor lighting is an example, not a mandatory group. Other switches or appliance actions may be added by installers. Dishwasher cycles or elevator modes are examples only: never infer appropriate behavior, religious approval, manufacturer support or hardware interlocks from an entity name.
- GR-FR-005: Distinguish observed status from action intent. A track-only group may appear on the timeline without executing anything. A trigger-style action (script/cycle) must not inherit replay/recovery semantics from an idempotent light state-setting action.
- GR-FR-006: Gate execution on verified capability, action semantics, target ownership, policy approval and installation-specific constraints. Unsupported actions remain visible as unresolved and cannot activate. Existing controller/interlock responsibilities are not bypassed.
- GR-FR-007: Shared-resource dependencies span groups; evaluate conflicts across all groups, not just within a preset. Two labels for one physical load do not create independent ownership.
- GR-FR-008: Import/export versioned group configuration; new installations adapt fictional templates privately. All group forms, validation and explanations support the multilingual catalog system, initially English/Hebrew.

## Nonfunctional requirements
- GR-NFR-001: Adding a simple on/off group requires configuration, not a new compiler branch. Typed non-idempotent actions require a tested adapter contract.
- GR-NFR-002: Unknown action types/versions fail validation; preview remains unable to execute. Runtime adapters are allowlisted and reviewable.
- GR-NFR-003: Determinism, local/UTC dates, duplicate protection and traceable reasons apply to extension groups identically to core profiles.

## Acceptance examples
Add a fictional patio-light group without changing compiler source; preview candle-minus-20 on and dated 23:00 off. Add a track-only equipment group and verify zero execution intent. Reject unsupported cycle/elevator commands and cross-group ownership conflicts. Preserve shared access lighting when an unrelated room is unused. Translate all group labels/errors in both default languages.

## Boundaries
No live appliance/elevator behavior is authorized by this specification. Feature 001 implements only a fixed sample subset; this feature is the migration from that proof of concept to generic schedule/group definitions. Dependency/provider choices require the review in docs/dependencies.md before implementation.
