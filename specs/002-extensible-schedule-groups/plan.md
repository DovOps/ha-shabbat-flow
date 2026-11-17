# Implementation plan: planning foundation and next dashboard

Branch: `002-planning-foundation`. Features 002 and 003 share the next data model; feature 004 captures the later review loop. No additional runtime dependency or live HA access is needed for the fixture-based work below.

## Delivery order
1. **Calendar and room-use foundation:** validate supplied one/two/three-day snapshots and independent time-bounded sleeping/recreation uses. Return overlap diagnostics. Keep the working v1 dashboard unchanged while this API is internal.
2. **Generic schedule compiler:** typed group/action configuration, independently timed lighting and HVAC profiles, segment-scoped anchors, meal windows, shared-load union and cross-group conflict detection. Heating/cooling require explicit capabilities and parameters; script/cycle semantics stay separate. Add synthetic acceptance fixtures before connecting UI.
3. **Dashboard v2:** dated day panels, independent sleeping/recreation selections, early/standard/late/custom profile choices, meals per day, copy-day with review, combined timeline and EN/HE parity. Explicit v1 draft migration preview, never silent conversion.
4. **Feedback foundation:** preserve immutable plan revisions and period IDs, then implement manual ratings and future-draft proposals from feature 004. Observation import and trend analysis can follow once real read-only coverage is known.
5. **HA adapter review:** inventory existing calendar/status providers read-only, document future date coverage and capabilities, then review dependency choice. “Issur melacha in effect” supplies live status; dated snapshots supply advance planning. Native dashboard/integration packaging follows a reviewed adapter contract.
6. **Controlled execution:** separate authorization/recovery/ownership milestone after a shadow preview. Not part of this increment.

## Foundation decisions
- Snapshot boundaries are distinct from candle lighting. On adjoining days a candle anchor can precede or follow the segment boundary under supplied observance conventions; do not synthesize it from sunset or repeat the first day's offset.
- Period contains ordered contiguous segments, source ID/version, explicit Israel/diaspora setting and preparation coverage. Validate offset-aware times against IANA timezone; no live calendar computation.
- Room use is an interval plus purpose, profile reference and control choice. One room may serve multiple purposes across the period. Overlapping uses produce diagnostics until an explicit conflict/precedence policy is implemented.
- Profile catalogs and physical-load mapping are supplied separately from household selections. Early/standard/late are editable profile labels, never inferred ages or identities.
- Existing v1 compiler stays isolated. Foundation validation is not schedule compilation, plan approval or device control.

## Review checkpoints
Checkpoint 002A: schema/validation, fixtures, tests and plan. Checkpoint 002B: generic compiler and migrated preview. Checkpoint 002C: dashboard with day-by-day room/meal planning. Record actual completion and limitations at each checkpoint; commit/push only when requested.

## Open production decisions
Exact provider/version and future-date API; subsequent-evening conventions; freeze/late-edit policy; source mismatch behavior; shared-load precedence and per-zone HVAC capabilities. None blocks synthetic schema work, but each must be resolved before production activation. Optional MCP/chat support is specified in feature 005. Its implementation/transport selection is deferred; dashboard and chat will share application services.
