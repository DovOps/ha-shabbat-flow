# Verification plan and traceability

Status: specification reviewed against the existing household, API, frontend and compiler code. Implementation and deployment checks below are pending; no wizard behavior is claimed as delivered.

| Scenario / evidence to add | Requirements |
| --- | --- |
| Select rooms, multiple purposes, navigate Back/Next/Skip, summary/Edit | WIZ-FR-001, 002, 011; WIZ-NFR-002, 008 |
| Save, reload/resume, failed write, offline, duplicate submit, concurrent browser revision | WIZ-FR-003, 013; WIZ-NFR-005 |
| Draft/skipped room creates no direct or shared actions; visible exclusions | WIZ-FR-004, 008; WIZ-NFR-006 |
| Area candidates, show all, renamed/moved/deleted/disabled entities | WIZ-FR-005, 013; WIZ-NFR-007 |
| Shared bathroom mapped once, multiple links, removed link, unresolved bathroom | WIZ-FR-006, 008; WIZ-NFR-006 |
| Bathroom intervals overlapping/touching/disjoint; whole 1/2/3-day period; home/away/unset | WIZ-FR-007; WIZ-NFR-006 |
| Copy current heat/cool, off/unavailable/unsupported states, incompatible devices, independent lead time | WIZ-FR-009, 010; WIZ-NFR-003, 007 |
| Legacy settings preserve mappings and semantics; workspace snapshot unchanged | WIZ-FR-012; WIZ-NFR-009 |
| EN/HE catalog parity, RTL, keyboard focus/errors, 360px mobile and desktop | WIZ-NFR-001, 002 |
| Admin access, request limits, own-store-only writes, fictional fixtures, zero device calls | WIZ-NFR-003, 004 |
| Automatic upcoming dates/manual override regression; HA version matrix; versioned package | WIZ-FR-011; WIZ-NFR-009, 010 |

Required commands: Python unit suite, Node web suite, repository hygiene, generated-package check and both supported HA integration suites. Record counts and live verification only after executing them.
