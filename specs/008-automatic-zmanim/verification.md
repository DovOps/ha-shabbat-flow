# Verification — automatic zmanim 0.3.0

- 62 Python compiler/server tests and 21 Node tests pass. Node coverage includes complete automatic snapshot transfer, explicit manual override initialization, preserved manual dates during refresh and hidden default manual controls.
- 28 HA tests pass on HA 2026.8.2 and 2026.11.2. New coverage includes provider registry discovery, admin guard, manual-source option, timeout, disabled/multiple providers, missing/duplicate events, one/two/three-day coverage, active-period rollover and offset-aware DST dates.
- Actual Jewish Calendar event generation is exercised with its declared hdate dependency for ordinary Shabbat, Israel/diaspora Rosh Hashanah and diaspora Pesach Thursday/Friday followed by Shabbat. Fixtures use a generic location and never household configuration.
- Source review confirms `calendar.get_events` is the only service read. No device calls, provider/registry changes or automatic fallback calculations.
- Build drift and repository hygiene checks pass. Live deployment acceptance completed below.

## Traceability
CAL-FR-001–003 / NFR-001–002: `tests/ha/test_upcoming.py`, discovery/assembly and real-provider contract tests.
CAL-FR-004–006 / NFR-003: automatic/manual Node regression, existing calendar/date/DST tests and EN/HE catalog parity.
CAL-NFR-004: CI HA/hdate version matrix.
CAL-NFR-005: new 0.3.0 full static path, rollback backup and live acceptance below.

## Installed acceptance
The integration was backed up, package checksum and Python syntax verified, upgraded and restarted under the explicit deployment authorization. All installed files matched final package SHA-256 `b2fd7a3fba09ee9a7b562852e0df083c83c71c29d17af51323995763ed781cf0`.

The installed 0.3.0 panel retrieved the next Shabbat's candle lighting, dated Saturday sunrise and final Havdalah automatically from Jewish Calendar, including its configured timezone and Israel observance. Manual fields were hidden by default. Enabling the advanced override populated all dated fields from the automatic snapshot; returning to automatic mode restored the summary. Calendar refresh completed successfully. English and Hebrew/RTL were visually checked. No household mappings were saved for testing and no device controls or provider settings were changed. Screenshots remain outside the repository.

Future multi-day cases are verified using actual-provider synthetic tests, not by modifying the live provider's calendar/location settings. Companion-specific testing remains pending.
