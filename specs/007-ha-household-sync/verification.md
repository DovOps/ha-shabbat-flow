# Verification — HA household synchronization 0.2.0

## Automated evidence
- 62 Python unit tests pass: deterministic compiler, intervals, calendar bounds, shared loads and server contracts.
- 19 Node tests pass: multilingual parity, DST/date controls, independent room purposes, planner drafts, versioned bridge routes and refresh preserving form-bound drafts, dirty edits and stale-write protection. The translation scan now anchors function names so URLSearchParams.get is not mistaken for a translation call.
- 13 HA integration tests pass on each of **2026.8.2** and **2026.11.2** with Python 3.14. Tests use actual registry and Store helpers with synthetic inputs; HTTP registration and config-entry access are mocked. They cover stable identity, inherited areas, floors, rename/move/delete/add, disabled/unavailable states, HVAC constraints, persisted reload, storage failure, stale writes, admin guards and body bounds, workspace snapshots and shared-load compilation.
- Generated package drift, ZIP allowlist and repository hygiene checks pass. No real inventory, private mappings or screenshots are tracked.

## Requirement traceability
| Requirements | Evidence |
|---|---|
| FR-001/004, NFR-003 | Registry identity/drift, inherited area/HVAC, floor/deleted-area tests |
| FR-002/005 | Frontend polling regression; persistence/revision/storage failure tests |
| FR-003/006/007 | Settings validation, personalized workspace/shared identity and workspace API snapshot tests |
| FR-008 | EN/HE catalog coverage; browser acceptance recorded below |
| NFR-001/002 | Admin/body-bound tests; scoped Store, API/bridge no-actuator review |
| NFR-004 | Both pinned HA versions in CI matrix and local test environments |
| NFR-005 | Versioned whole asset tree, deterministic ZIP and backed-up upgrade |

## Scope limits
Preview only and admin only. Full future multi-day calendar acquisition, non-admin family access, execution, feedback persistence and MCP remain deferred. Weekly plan snapshots remain browser-local. Meal device groups need explicit advanced configuration; they are not inferred from area names. Generated room profiles are editable starting examples, not historically learned defaults. HVAC scheduling currently requires supported fan-mode metadata. Automated tests do not replace Companion/browser checks.

## Deployment acceptance
The upgrade archive checksum and Python syntax were verified before extraction, and the prior integration was copied outside custom_components for rollback. HA restarted successfully and the versioned 0.2.0 setup page loaded actual registry areas and entities. English and Hebrew/RTL rendered at full viewport height. Candle-lighting/end date controls populated from Jewish Calendar; next-morning sunrise remained explicitly unresolved. An unsaved room was marked for both sleeping and recreation, refreshed without losing either choice, then discarded. No real household mappings were saved and no device commands were sent. Personalized compilation/persistence remain verified with synthetic fixtures; household-specific end-to-end plan review is left to the installer. Companion testing remains pending.

The final archive SHA-256 is `43fe9f78b898ef4ab82120f678dca2b19cc5a2fe5eae1649376a0f0e74383bb7`. Every installed package file was compared byte-for-byte with that archive. The updated installed fictional demo generated its 25-event preview. House setup was left open for installer testing. Browser screenshots stay outside the repository.

## Planner button feedback correction
Reproduced offscreen, misleading date validation on the installed panel. A separate live tab now displays specific prerequisites beside the button and focuses that message. The original editing tab was preserved. Tests: 62 Python and 20 Node tests pass; the new lifecycle regression covers missing fields, unsaved setup, server failure, duplicate-submit suppression, successful navigation and browser-storage failure. EN/HE catalogs remain complete.

Only household.html, household.mjs and household-i18n.json were deployed, with a prior integration backup and byte-for-byte verification against package SHA-256 `5c80f65cd16f4ddbd33754686064cff242b1b9965bf990ef7a469d29eababdd2`. No HA restart or household configuration writes. Script/catalog query versions invalidate their caches, but an existing cached HTML document requires a browser hard refresh once, after saving edits. The visible corrected error path was verified in Chrome; successful creation is covered by synthetic tests, not a newly saved real household configuration.
