# Internal planning foundation (v2, not yet a public API)

`planning.validate_calendar(snapshot)` validates a supplied snapshot and returns parsed UTC instants and IANA timezone information. Required fields:

- `schema_version`: integer 2; `period_id`: stable identifier.
- `timezone`: IANA name; `observance`: `israel` or `diaspora`.
- `source`: bounded `id` and `version` strings. The future provider contract will add calculation settings/freshness; these two strings alone are not sufficient production provenance.
- `preparation_start`, `start`, `end`: offset-aware minute-resolution timestamps consistent with the timezone. Preparation is at most 24 hours before start; total active span is bounded to 96 hours.
- `segments`: 1–3 ordered contiguous segments, each with unique `id`, `kind` (`shabbat`/`yom_tov`), `start`, `end`, `candle_lighting`, and `sunrise`. First/last boundaries equal period boundaries. Sunrises advance one local calendar date per segment. Candle anchors are supplied separately from boundaries and must progress after the preceding sunrise.

This validates temporal structure, not the religious accuracy of supplied dates or zmanim. Synthetic tests deliberately are not a holiday calendar implementation.

`planning.validate_room_uses(snapshot, uses, room_ids, profiles)` validates up to 300 uses against at most 100 room IDs and 100 profile references. `profiles` maps a stable profile ID to its purpose; actual timing/HVAC configuration is future compiler work.

Each use has unique `id`, known `room`, `purpose` (`sleeping`, `recreation`, `other`), `control` (`planner`, `existing`), `profile` (matching reference for planner, null for existing), `start`, and `end`. Uses are half-open intervals inside preparation/end coverage and can cross segment boundaries. All overlapping same-room uses produce deterministic possible-conflict records. Adjacent uses do not conflict. This deliberately does not resolve shared physical loads or profile compatibility yet.

These foundation functions alone do not generate schedules or approve plans. The subsequent generic compiler adds meal/home-away models and a v2 preview HTTP endpoint; see contracts/compiler-v2.md. Browser-local draft storage is separate from v1. Production persistence, migration and activation remain absent. Existing v1 preview remains unchanged. Source/status reconciliation, capability checks and full production provenance remain required before activation.
