# Checkpoint 017 — public guides and app presentation

## Delivered

- English/Hebrew developer guide makes root AGENTS.md and agent-assisted spec-driven development explicit, with a reusable starter prompt.
- Gallery contains three reviewed real-interface captures using fictional fixtures, with version labels, translated captions and capture provenance.
- Product display name is Shabbat Flow. Only the exact legacy default config-entry title migrates; customized titles remain intact.
- App navigation uses active-page tabs. Available dependency tiles use pale lime green; setup-needed and missing states retain distinct styling and text/icons.
- Functional/nonfunctional requirements, plans, task status and roadmap updated.

## Verification

- Python core: 76 tests passed; JavaScript: 48 tests passed.
- Home Assistant integration tests: 107 passed on 2026.11.2 and 107 on 2026.8.2, including default-title migration/custom-title preservation.
- Website production build passed in English and Hebrew. Checker verified 130 pages and 5,472 project-relative links/assets, canonical spec coverage and 0.15.1 metadata.
- Local desktop visual review confirmed the Hebrew gallery, active navigation and full lime-green available cards. Gallery screenshots were inspected before inclusion.
- Package: `shabbat-flow-0.15.1.zip`; SHA-256 `5acd40f8e2cd4778965031f02bcf628ad3d7132288b32900f215c45264e87cee`.

## Rollout boundaries

Local website refreshed and package prepared. HA remains on 0.15.0; no installation, restart, device control or notification delivery occurred in this checkpoint. Public Pages deployment still requires owner enablement. Gallery screenshots show labeled earlier capture versions rather than claiming all are current-release screens.
