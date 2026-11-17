# Feature specification: continuous Shabbat and Yom Tov planning

Status: requirements draft; not implemented in the single-Shabbat preview.

## User scenarios
A household plans the whole upcoming observance before it starts, whether one day, two days, or three consecutive days. Each evening/day has its own meals, sleeping/recreation uses, lighting and HVAC profiles. Copying a day is an explicit convenience; it does not silently assume identical plans.

The preferred live status source is the configured “issur melacha in effect” entity. Future calendar data supplies dated boundaries and anchors. An on/off signal alone cannot tell the planner when future meals, sunrise or the next evening occur.

## Functional requirements
- MD-FR-001: Model a continuous observance period containing ordered dated segments, each categorized as Shabbat or Yom Tov (with optional holiday metadata). Support at least one, two and three consecutive days, including two-day Rosh Hashanah in Israel and Shabbat adjoining two-day Yom Tov in diaspora settings. Israel/diaspora observance is an explicit installation setting, independent of UI language and timezone.
- MD-FR-002: Map the live active-state signal to an owner-selected entity; preserve on, off, unknown and unavailable distinctly. Do not infer a specific integration from its display name. Missing/contradictory status and calendar coverage must be visible. Before execution, define and test mismatch/outage policy; unknown is never treated as off.
- MD-FR-003: Require future dated coverage for the full period, including preparation before its start, each evening’s applicable candle-lighting anchor, each sunrise and the final agreed end. Preserve source, calculation/observance settings, timezone and snapshot version. Never infer future boundaries from binary transitions or blindly add 24 hours.
- MD-FR-004: Provide dated meal slots per segment (evening/daytime and configurable additional meals), with away, household or hosting choices and explicit unset status. Permit a no-meal profile; never assume every holiday has meals. Separate meal setup, serving and cleanup windows where configured. All required choices must be resolved before approval.
- MD-FR-005: Plan home/away and room uses by time window, including overnight stays across segment boundaries. Apply shared-resource dependencies across all overlapping uses. Keep independent lighting and HVAC offsets and room-specific sleep/wake profiles; do not reset occupancy or turn everything off at an internal day boundary.
- MD-FR-006: Every relative rule identifies its dated anchor and segment explicitly. Evening offsets remain relative to applicable candle lighting, not sunset. First-evening and subsequent-evening candle times are separate provider-supplied values under the owner’s conventions; do not assume a later evening uses the first evening’s pre-sunset offset. Sunrise offsets and fixed local times remain distinct. Show actual dates and times in the preview.
- MD-FR-007: Compile and approve the entire period before its earliest preparation action. Freeze one version covering all segments. Internal calendar changes or the active signal staying on do not require a new manual activation or terminate the plan. Late changes require an explicit future execution policy, not a hidden automatic recompile.
- MD-FR-008: Show a whole-period overview and separate dated day panels with meal and room-use completeness, per-day overrides and a combined timeline. Offer explicit copy-to-next-day with review of resulting times. Label source status and future coverage separately. Support English/Hebrew and RTL through multilingual catalogs.
- MD-FR-009: Resolve shared loads and contradictory events across segment boundaries as well as within a day. Give each event stable period/segment/rule identity. Keep per-night catch-all rules and temporary extensions scoped to a specific dated night, with one owner.
- MD-FR-010: End-of-period restoration occurs only at the final agreed end under the approved execution policy. Existing boiler or other automation suspension, when selected, spans its configured window without accidental restoration at intermediate day boundaries.

## Data model direction
A versioned period contains `period_id`, timezone, observance settings, start/end and provenance; ordered segments contain stable IDs, local dates, categories and named dated anchors. Meals and room-use windows refer to segment IDs or explicit intervals. Rules reference anchors explicitly. Live sensor observations are separate from the immutable calendar snapshot and plan digest. Version 1 drafts remain readable via an explicit migration; do not reinterpret their Friday/Saturday fields silently.

## Nonfunctional requirements
- MD-NFR-001: Identical normalized inputs and calendar snapshot produce identical events/digest, irrespective of language or current sensor rollover.
- MD-NFR-002: Compare instants in UTC, display with the configured IANA timezone, and validate ambiguous/nonexistent fixed local times. Elapsed offsets and calendar-day recurrence must remain distinct across DST.
- MD-NFR-003: Full-period coverage and validation errors block approval; never silently truncate a three-day plan to one day. Bound period/event sizes and document supported limits before implementation.
- MD-NFR-004: Synthetic fixtures only; no home-specific entity IDs or family information in the repository. No new calendar dependency without owner review.

## Required acceptance cases for implementation
1. Ordinary Shabbat: one evening/day, independent meals and room profiles.
2. Two-day Rosh Hashanah under Israel settings: separate meals and anchors; no intermediate reset.
3. Two-day Yom Tov followed by Shabbat, and Shabbat followed by two-day Yom Tov: three-day timelines, distinct evening conventions, final restoration only once.
4. A live sensor remains on throughout: segment two/three events still occur from the approved dated plan.
5. Different meal/home/room selections per day, overnight shared-bath dependencies and overlapping cross-day rules.
6. No-meal profile and additional meal slots; unset required selections block approval.
7. Missing final-day anchors, source rollover, unavailable sensor or conflicting status: visible diagnostics and no implicit approval or early restoration.
8. DST, midnight-crossing offsets, fixed nightly catch-all and per-night extensions; locale change leaves event identity unchanged.

## Implementation sequence and review points
First settle the provider contract and inspect available future coverage read-only. Then implement a versioned period schema and compiler fixtures, followed by the dated multi-day dashboard, migration and full-period validation. Add execution/status reconciliation only in the separately reviewed executor phase. Confirm provider(s), subsequent-evening conventions, freeze timing and mismatch/outage behavior before production activation.

The current compiler deliberately still rejects multi-day input. This specification promotes multi-day planning to the integration foundation rather than promising it in today’s preview.
