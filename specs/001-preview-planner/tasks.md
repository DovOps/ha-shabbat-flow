# Tasks: preview planner

## Foundation
- [x] T001 Record constitution, product roadmap, official Spec Kit template provenance and privacy boundary.
- [x] T002 Inspect Good Days and document reuse decision in research.md.
- [x] T003 Specify contracts, model, multilingual acceptance criteria and traceability.

## US1: household preview
- [x] T004 Write tests for resource union, away contradictions, invalid mappings and deterministic output in tests/test_compiler.py.
- [x] T005 Implement fixture configuration and compiler in src/shabbat_flow/compiler.py.

## US2: independent timings
- [x] T006 Test candle/sunrise/fixed times, independent HVAC offsets, midnight and DST validation.
- [x] T007 Implement validated timestamp handling and event conflict detection.

## US3: multilingual interactive preview
- [x] T008 Create complete EN/HE catalogs and key parity tests.
- [x] T009 Implement loopback preview API and transport security tests.
- [x] T010 Implement responsive RTL/LTR dashboard, explicit browser save/load/delete/export and localized failures.
- [ ] T011 Final browser recheck: initial EN/HE interactions, mobile overflow and keyboard labels verified; follow-up permission was declined. New sleep-light/HVAC wording visual check remains pending. See verification.md.

- [x] T014 Add independently adjustable bedroom sleep-light cutoff with homeowner-defined per-room loads and tests (FR-011).

## Checkpoint
- [x] T012 Add CI, hygiene gate and document performance/verification evidence.
- [x] T013 Reconcile requirement coverage and limitations; stop before commit/push.

Dependency order: foundation → tests/compiler → UI/API → verification. No production installation task belongs to this feature.
