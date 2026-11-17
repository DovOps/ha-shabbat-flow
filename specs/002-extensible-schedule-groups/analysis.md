# Foundation traceability and verification

2026-11-17: 39 Python and 5 Node checks pass; repository hygiene passes.

| Scope | Evidence | Limits |
|---|---|---|
| MD-FR-001, 003, 006 temporal foundation | `tests/test_planning.py`: 1/2/3 segments, both Shabbat/Yom Tov orders, separate candle anchors, missing final coverage | Supplied synthetic times; no calendar provider or religious date validation |
| MD-NFR-002 timezone handling | DST 23-hour span, invalid timezone offset and nonexistent local time cases | No calendar recurrence resolver yet |
| GR-FR-009, 011 room-use foundation | Sequential recreation/sleep, cross-boundary use, stable overlap diagnostics, existing-control choice | Not exposed in dashboard; no shared-load resolution |
| GR-FR-010 profile reference foundation | Unknown reference and purpose mismatch rejection | No profile timing/mode compilation yet |
| Bounded strict validation | Duplicate IDs, oversize uses/segments, unknown fields, invalid types, out-of-range uses | Internal functions, no new network endpoint |
| Existing behavior | Original 25 Python and 5 Node tests remain passing | Existing v1 dashboard still single-Shabbat/sleeping-only |

Feature 004 feedback and feature 005 MCP/chat are specifications only. No AI/MCP/calendar dependency has been adopted; no HA change or deployment occurred. New work remains uncommitted on `002-planning-foundation`. No browser verification was needed or attempted for this internal-only increment.

## Generic compiler and v2 dashboard checkpoint

Implemented `schedule.py` and the opt-in `/v2` preview (see contracts/compiler-v2.md). The v1 page/API/storage remain separate. Generic binary/HVAC groups support points and maintained intervals, shared physical aliases, explicit owners, typed heating/cooling with temperature/fan capability checks, profile references, per-segment relative anchors and dated fixed times. Track-only entries cannot become command intents. The compiler never controls devices.

`tests/test_schedule.py` covers full three-day output, independent HVAC timing, home/away contradictions, no-meal periods, missing selections, overlapping room uses, incorrect profile mappings, shared bathroom coverage, cross-day continuity, aliases/ownership, conflicting cutoff points, HVAC modes/units/limits, adding outdoor groups by configuration, track-only behavior, existing-control choices, unsupported actions, bounded expansion, determinism and language independence. HTTP tests verify v2 routes, validation, origin restrictions, and absence of activation; Node checks cover translated keys, profile filtering and separate draft storage.

Actual verification: 61 Python + 9 Node tests pass (70 total), syntax and repository hygiene checks pass. No HA data or external code/dependency was incorporated. No browser verification was attempted because prior browser access was declined. Keyboard, responsive layout and RTL behavior are implemented but not newly verified visually. No updated screenshots are claimed.

Outstanding: v1 migration, copy-day, scene/script/action adapters, richer guided profile editing (currently advanced JSON), post-observance feedback storage, live provider inspection/compatibility, approval/freeze, execution/recovery and browser UX verification. `complete: true` is draft/compile completeness, not production approval. Source metadata remains illustrative, not verified zmanim provenance.

## Family UX and branding revision

The default `/v2` view now shows one dated day at a time, home/away, sleeping and recreation tiles, meal choices and a readable summary. Technical editors are collapsed under Advanced setup. Room overlaps and away/selected-room contradictions have contextual explanations and explicit correction actions. Optional independent bedroom HVAC/light sliders clearly state that defaults affect every day using the profile. Custom multi-use windows are preserved and routed to advanced review.

Copy previous day stages choices for explicit review/application; tests cover preservation of source/manual selections, unique IDs, local-clock copying across DST, ambiguous/nonexistent-time rejection and period bounds. Room-profile defaults are optional configuration and do not override custom windows. Generated logo text now emphasizes HA and uses the approved tagline.

Validation: 61 Python + 16 Node tests (77 total), JavaScript syntax and repository hygiene pass. Browser visual/interaction verification remains pending; no fresh screenshot or verified responsive/RTL claim is made. Ngrok was explicitly shut down and remains off. No HA changes or third-party implementation dependencies were introduced.
