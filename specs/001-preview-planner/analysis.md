# Requirements analysis / traceability

No preview-blocking unresolved requirement: supplied synthetic calendar anchors are explicit; live calendar, actuator mapping and execution policies are deferred, not inferred.

| Requirement | Verification |
|---|---|
| FR-001,006 | schema/type/date/version/contradiction tests |
| FR-002,003 | alternate configuration, union/missing reference/conflict tests |
| FR-004,005 | candle offset, sunrise, midnight/DST, independent offset tests |
| FR-007; NFR-003 | catalog parity/code coverage, browser EN/HE/RTL/mobile/keyboard checks |
| FR-008 | save/load/delete/export browser checks; malformed storage and state validator tests |
| FR-009; NFR-002 | code review: no HA client/dependencies; allowlisted local server |
| FR-011 | selected-room sleep cutoff, independent timing, empty list and protected resource tests |
| FR-010 | sample banner and explicit timestamp controls |
| NFR-001 | repeat compilation and locale-independent digest test |
| NFR-004 | payload/schema limits, wrong Host/Origin, path rejection tests; textContent rendering |
| NFR-005 | repository hygiene script and final diff inspection |
| NFR-006 | 100-run compiler benchmark |

Before implementation: architecture meets constitution; multilingual behavior is included in this feature, not deferred. Check verification.md for executed evidence and limitations.
