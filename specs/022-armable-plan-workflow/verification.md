# Verification — stage 1

Implemented and locally verified; not deployed to HA. Scheduled control remains lighting-only. No household plan or observation was modified, no device calls were made, and no run was armed.

- AW-FR-001–004: native collapsible command drawer, grouped secondary commands and read-only status cards separate draft, control, plan observation and climate study. Approved status remains explicitly not armed. Compact control listings include the next pending event without full history.
- AW-NFR-001: fictional browser fixture checked in English and Hebrew, including RTL, keyboard drawer activation, grouped menu and collapse after mobile navigation. At 360 CSS pixels the collapsed sticky bar measured approximately 61 pixels high. Initial mobile collapse does not overwrite a deliberate per-tab preference. Physical phone acceptance remains pending.
- AW-NFR-002: dedicated admin-only status operation skips inventory discovery; frontend has one in-flight request, visible-page 30-second polling and five-second focus throttle. Refresh failure retains prior data with a stale notice. Backend regression verifies discovery is not called and status performs no device service calls.
- AW-NFR-004: fictional fixtures only; no new dependencies or production operations.

Checks: 94 core unittest tests; 72 Node web tests; 19 execution tests on each of HA 2026.8.2 and 2026.11.2. All passed. Repository hygiene, generated bundle consistency and whitespace checks passed. HA test environments emit five existing deprecation warnings each.

Stages 2–4 remain pending: evidence reuse/invalidation, unattended ownership review, authoritative draft-versus-frozen comparison, qualified scheduled HVAC/fan adapters and recovery coverage, unified outcomes/adoption guidance, coordinated deployment and owner-supervised timed pilot. Existing rehearsal success is not scheduled-control qualification.
