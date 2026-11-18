# Feature 008 — Upcoming observance and automatic zmanim

Approved scope: read Jewish Calendar automatically, move manual dates into Advanced settings, deploy preview update. No device execution or changes to provider configuration.

## Functional requirements
- CAL-FR-001: Default household setup to the next not-yet-started complete Shabbat/Yom Tov period. Show readable local dates, observance, source and each day's candle lighting, sunrise and end.
- CAL-FR-002: Discover one Jewish Calendar config entry and its enabled daily/yearly calendars by registry provider/translation keys. Use only `calendar.get_events` (read-only). Use provider timezone and Israel/diaspora configuration; never infer them from display names. Multiple providers, missing calendars/events and invalid times produce explicit localized guidance, with no silent fallback.
- CAL-FR-003: Retrieve a bounded date range, assemble 1–3 consecutive days through final Havdalah, and validate daily coverage. Intermediate candle-lighting anchors remain provider-supplied. Saturday segments are Shabbat; other days within the observance are Yom Tov. Segment transitions use the next day's candle-lighting anchor (planning boundaries, not a claim of halachic day boundaries). Reject incomplete/ambiguous coverage.
- CAL-FR-004: Automatic creation copies the complete snapshot into a new workspace. No date entry required. Refresh calendar explicitly, independently of room edits. Already-open workspaces remain immutable snapshots until explicitly edited.
- CAL-FR-005: Advanced settings offer an explicit manual override, with labelled date/time controls, observance and type. Prepopulate from automatic first-day data only when switching into manual mode; clearly label the override and single-day scope. No refresh overwrites manual edits. Existing advanced planner can extend supplied segments.
- CAL-FR-006: Missing/stale automatic data blocks automatic creation and directs the user to configure the provider or deliberately use manual mode. Show actionable feedback beside the action; preserve unsaved household edits.

## Nonfunctional requirements
- CAL-NFR-001: Admin-only API, bounded lookahead (14 days plus 4 prior days), timeout, allowlisted calendar reads only. No raw event descriptions, location coordinates, credentials or config exports. No new external dependency.
- CAL-NFR-002: Keep all instants offset-aware in the provider's IANA timezone, including DST. Never use today's sunrise for another date, shift sunrise by 24h, or invent missing candle-lighting times.
- CAL-NFR-003: EN/HE catalogs and RTL for automatic summaries, errors and manual mode. UI default hides manual date controls.
- CAL-NFR-004: Synthetic unit/integration tests cover single/two/three-day periods, Israel/diaspora, DST, provider discovery, disabled/missing/ambiguous sources, timeout, incomplete/duplicate dates, boundary rollover, manual override preservation and workspace snapshot use. Test HA 2026.8.2 and 2026.11.2.
- CAL-NFR-005: Version the full static tree; back up installed integration and preserve stored mappings. Verify real automatic dates after restart without saving test mappings or controlling devices.

## Limits
Only the next period is automatically selected. Custom date selection, multiple-location provider selection, automatic activation, family access and future non-Jewish-Calendar adapters are separate work. An observance already underway is skipped, avoiding a new plan whose first actions have passed.

## Optional bathroom daylight anchor
- CAL-FR-007: Supply optional dated `sunset` per segment from the existing Jewish Calendar daily Shkia event. Require a unique valid aware timestamp after sunrise on the same local date. Missing/duplicate/malformed optional sunset must not invalidate otherwise complete candle/sunrise/end coverage; omit it and let bathroom daylight policy retain lighting with a preview warning. Test actual provider events on both supported HA versions. No sunset substitution for candle lighting.
