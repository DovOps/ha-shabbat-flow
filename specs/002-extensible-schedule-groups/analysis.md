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
