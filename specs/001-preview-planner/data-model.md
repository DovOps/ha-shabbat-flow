# Data model v1

Configuration: schema_version=1; loads (max 100) keyed by stable logical ID, each with en/he labels; rooms with multilingual labels, `wall` and `climate` load references plus `sleep_lights` list (may be empty, cannot target protected shared-dependency loads); dependencies with nonempty rooms/loads references; roles naming supported generic resource arrays. Duplicate references union, not repeated commands.

Plan: schema_version=1; language en/he; timezone IANA string; candle_lighting, sunrise, end as offset-bearing ISO timestamps; home boolean; used_rooms array of unique known room IDs; dinner/lunch enum away/family/hosting; offsets `{bedroom_hvac, shared_hvac_off, night_lights, bedroom_lights}` integer elapsed minutes 0..720.

Strict known keys, bounded text/arrays, no arbitrary service names or templates. Offsets/timestamps must produce valid single-Shabbat windows. Fixtures have no real entity IDs. Production IDs belong in a private future adapter, not sample defaults.

Event: logical load ID, desired on/off, UTC ISO instant, local ISO instant, stable rule ID and event ID. Ordering by UTC/load/state/rule. Same-time identical load/state requests merge; contradictory ones produce a validation error. Reasons are translated from stable rule IDs in the UI. Result: preview_only=true, events, digest, earliest preparation time. Hash includes configuration and plan except language; no wall-clock generation timestamp.
