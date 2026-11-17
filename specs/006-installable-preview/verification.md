# Verification — installable preview 0.1.0

- 62 Python unittest tests: compiler, periods, groups, server boundaries and timestamp second precision.
- 17 Node tests: EN/HE catalog parity, draft/model behavior, room/meal choices, copy semantics and DST-aware date entry (gap rejection, fold choices, second preservation).
- 6 tests against installed Home Assistant **2026.11.2**, Python **3.14**, pytest **9.2.0**, pytest-asyncio **1.5.0**: actual panel/registry classes, setup/unload/reload; admin request checks; compiler parity; malformed and oversized streamed bodies; selected/missing/manual calendar values; provider registry discovery/ambiguity; setup form/duplicate prevention/options schema. HA emits upstream deprecation warnings.
- HA tests mock HTTP route registration and config-entry access; requests are synthetic. They do **not** verify a full running HA authentication pipeline, actual config-entry installation or a browser/Companion session.
- Generated asset drift check and deterministic ZIP build pass; exact allowlist excludes test environments and private files. SHA-256 accompanies the ZIP.
- Repository hygiene checks pass. All example inputs are fictional; no live household configuration or credentials are included.

## Requirement coverage

| Requirement | Evidence |
|---|---|
| INSTALL-FR-001 / NFR-001 | `scripts/build_ha.py --check --zip`, versioned manifest, allowlisted generated package |
| INSTALL-FR-002 | `tests/ha/test_integration.py::test_real_panel_lifecycle`, admin guard tests |
| INSTALL-FR-003 | API/bridge allowlists reviewed; no executor; compiler parity test |
| INSTALL-FR-004 / FR-006 | Calendar missing/manual/provider ambiguity/invalid timestamp tests; explicit selected-values-only coverage |
| INSTALL-FR-005 | `tests/web.test.mjs` DST/date tests and `test_calendar_second_precision`; browser interaction pending |
| INSTALL-NFR-002 | Pinned HA package tests and this scope disclosure |

## Remaining acceptance work

Live installation/version inspection is unavailable in this session because configured HA authentication is not accessible. No household installation, restart or device changes occurred. Browser visual, keyboard, RTL and Companion interaction checks remain pending. Full future calendar acquisition, non-admin family access, persistent shared plans, execution, feedback and MCP remain future iterations. Current sensor reads must not be presented as complete multi-day coverage.
