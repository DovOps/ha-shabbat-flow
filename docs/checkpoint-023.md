# Checkpoint 023 — flexible activities and comfort (0.17.0)

Implements Feature 014 planning and shadow-observation stages. Adds explicit meal duration/cleanup choices, multiple recreation/playtime/service windows with persisted calendar offsets, per-load exclusions and full replacement, bathroom daylight suitability, independent fan/outlet track-only intents, bounded conditional comfort decisions and classified feedback. HTML and PDF share effective meal times and policy summaries. English/Hebrew supported. Old saved schedules remain unchanged until explicitly edited.

Verification: 91 core tests, 60 JavaScript tests, 113 HA tests on each supported version (2026.8.2 and 2026.11.2). See feature verification for traceability and limitations. Live execution is not included, and no device controls are activated. Deployment outcome will be appended after installation verification.

Website validation: both locale builds passed; 146 pages and 6,456 project-relative links/assets checked, including canonical specs. Package SHA-256: `2d5a46f2ec61d6610b7539811143f5a598b8815897d0521c2f7d9025dfd62fc5`.

Visual follow-up: attached HH:MM inputs before the existing input helper replaces them. Browser editing from 01:30 to 01:45 changed the compiled meal release by 15 minutes. This frontend correction does not require an additional HA restart.

## Deployment verification
Authorized installation completed with package checksum validation, 55-file parity, component backup and all three existing saved-data stores preserved. One HA restart loaded the new backend. Final HH:MM correction was static-only and required no second restart. The live household setup and saved plan reopened; the new meal preset produced a successful schedule preview with no save or observation activation. The HA shell still displayed its general startup notice during this integration check; no claim of a full-system health audit is made. No device or existing automation was controlled or modified.
