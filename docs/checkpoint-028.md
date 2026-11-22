# Checkpoint 028 — exact-plan rehearsals (0.21.0)

Feature 019 adds actual compiled moments to the planner, separate transition versus setup-at-a-moment simulation, explicit area/device selection, immediate supervised binary-lighting tests, and reviewed restore. Snapshot dates/anchors and the upcoming weekend execution ledger remain unchanged. Shared bathrooms require explicit selection. Existing writer conflicts, inactive-observance checks, state/context drift checks, atomic intent, idempotency and overlap reservations apply. Restarts interrupt rather than resume; no retry or automatic restore. HVAC, fans and appliances remain simulation-only.

Private history retains up to 20 tests/90 days, supports feedback and exact-plan JSON export. English/Hebrew help and the website setup guide explain the workflow. No new dependency. See `rehearsing-a-plan.md` and Feature 019 requirements/verification.

Verification: 94 core tests, 67 JavaScript tests, 154 HA tests on each of 2026.8.2 and 2026.11.2 pass. Repository hygiene, generated asset parity and whitespace checks pass. Both website locales build and project-relative link checks pass. Package SHA-256: `c44655761a91cc54a4d6cd3d13b628aff8b59781cfba22858c5123ef0a13a006`.

Deployment is pending: this session's browser tool reports local browser access unavailable, and the existing public HA host's SSH port is unreachable. No production files or device states were changed and no plan was armed. Browser visual/keyboard acceptance and owner-supervised real-device testing remain pending; automated service spies do not certify physical hardware.


Deployment verified after access was restored: 71 packaged files byte-verified, three existing saved-data files preserved unchanged, on-host integration/storage backup, and one HA restart. The versioned 0.21.0 UI loaded with all 20 saved rooms ready. Exact-plan scenario discovery and read-only simulation succeeded against an existing saved plan; no rehearsal was applied and no control run was scheduled. Fictional EN/HE layout, area selection, simulation and keyboard activation were checked. Owner-supervised physical tests and mobile acceptance remain pending. Both GitHub checks and website publication passed for the implementation commit.
