# Feature specification: post-observance feedback and improvement

Status: partially implemented. Feature 015 supplies an owner review linked to an observation, optional ratings, classifications, revision history and exports. Full multi-person, comparable-cohort trends and automatic proposal workflows remain specified, not implemented. This feature does not require a chat protocol or AI service.

## User scenarios
After an observance, household members record how well the plan worked. An owner reviews ratings alongside the approved plan and available observations, then chooses changes for a future plan. The workflow covers every day of a multi-day period, with an optional whole-period summary.

## Functional requirements
- FB-FR-001: Link feedback to the exact period, segment and executed/frozen plan revision, or explicitly mark a draft-only review. Preserve the original plan and distinguish planned actions, executor outcomes, device observations and reported experience. A successful command does not prove comfort or occupancy.
- FB-FR-002: Offer optional 1–5 ratings with consistent meanings: 1 very poor, 2 poor, 3 acceptable, 4 good, 5 excellent. Include overall fit, lighting fit and HVAC comfort; allow not applicable and unanswered separately. Include room/group, meal or time-window detail where relevant.
- FB-FR-003: Ask what differed from the plan: actual room purposes, meals, timing, light levels, too hot/cold, pre-conditioning and wake-up comfort, access/bathroom lighting, late activity, manual interventions and device failures. Record reported experience as a report, not verified sensor evidence. Do not request religious identity or infer who operated a switch.
- FB-FR-004: Record whether an issue was one-time, recurring or uncertain, its impact, and any requested timing/profile adjustment. Track favorable outcomes as well as problems. Preserve conflicting responses rather than choosing a family member's opinion automatically. Names are not required; optional household-local pseudonyms must not enter repository fixtures.
- FB-FR-005: Compare approved events against observations using explicit configurable timing tolerances and actual history coverage. Report matched, late, missing-observation, contradictory-state and unassessed results. Keep unknown separate from failure; account for gaps, unavailable entities, boundary intervals and shared physical-load aliases. Never infer recreation, sleep or actual occupancy solely from lights/HVAC.
- FB-FR-006: Show trends for comparable profiles/season/observance/event categories, with sample sizes, response counts, missing answers and plan versions. Keep special events distinct from ordinary weekends. Do not describe repeated responses from one period as multiple successful Shabbat trials. Show rating distributions and denominators, not only a misleading combined score.
- FB-FR-007: Propose a future revision with old/new values, affected rooms/days/actions, evidence, sample size, uncertainty, known exceptions and a preview of the resulting timeline. A deterministic rule or optional AI may propose; neither can silently apply, activate or mutate a frozen plan. Owner accept/reject/defer decisions are recorded.
- FB-FR-008: Track proposal lifecycle: suggested, accepted for a future draft, rejected, deferred and evaluated after a later period. Acceptance does not mean activation. Link later ratings to the applied revision so users can see whether an adjustment helped, without claiming causality from small observational samples.
- FB-FR-009: Support manual feedback without HA history or AI. Import/export a versioned review bundle for user-initiated analysis, with an explicit content preview. Raw history and free text remain local unless intentionally exported. Define retention, access and deletion settings before persistent production storage is enabled.
- FB-FR-010: Provide English/Hebrew forms, rating meanings, diagnostics and summaries through multilingual catalogs. Keep machine values language-neutral. Feedback can be entered after the whole observance ends; no interaction during observance is required.

## Sample family questionnaire
1. Overall, how well did the plan work? (1–5 / unanswered)
2. Which day, room, meal or time window does this feedback concern?
3. Were lighting and HVAC comfortable? (separate ratings / not applicable)
4. What happened differently from the plan? Was anything too early, too late or missing?
5. Were rooms used for sleeping or recreation differently than planned? Were meals different?
6. Was any intervention needed? What changed, approximately when, and why, if known?
7. Was this an exception or something to change for future weeks?
8. What worked well and should stay the same?
9. What single adjustment would help most next time?

## Data and nonfunctional requirements
- FB-NFR-001: Versioned feedback records reference immutable plan/period IDs and contain timestamps, typed optional ratings, scoped observations and bounded free text. Set size limits before API implementation. Corrections are explicit and auditable; deleting feedback removes it from derived summaries under the selected retention policy.
- FB-NFR-002: Aggregation and plan-versus-observation comparison are deterministic for the same inputs, tolerances and algorithm version. Optional AI narrative is labeled and is not part of deterministic scoring.
- FB-NFR-003: No secret, real household record, family name or actual history in reusable fixtures. Exports exclude credentials. Production authorization separates submitting feedback from accepting plan changes.
- FB-NFR-004: Missing history or feedback cannot increase confidence. Trends disclose coverage and comparison criteria. Dashboard and any later optional interface use the same validation and proposal lifecycle.

## Acceptance cases
A three-day period supports per-day and overall feedback without losing scope. Two conflicting room-temperature reports remain visible. A recorder gap yields unknown rather than failure. A one-off gathering is excluded from an ordinary-weekend comparison by explicit classification. An accepted adjustment changes only a future draft; its predecessor remains intact. Unanswered ratings do not become zero. The full feedback flow works without an AI service and in both default languages.

Feature 014 AC-FR-014 extends classification of deviations: intentionally new behavior and exceptional periods must remain distinct from unwanted mismatches. Reported fan-assisted comfort is separate from measured fan runtime. Household evidence stays local; generalized requirements alone enter the repository.
