# Feature 011 — Standalone climate studies

## Scope and clarification
Administrators can manually observe ordinary household climate use without calendar data, a complete room setup, a schedule or automation. This is evidence for comfort/setpoint review, not automatic thermostat calibration. Start immediately for 1–48 whole hours (default 24); stop early if needed. Scheduled starts and sending summaries are deferred. No new dependencies.

## Functional requirements
- CS-FR-001: Offer Climate Study directly from house setup; no Shabbat plan or Jewish Calendar is required.
- CS-FR-002: Select 1–100 enabled registered climate zones and 1–48 hours. Explicitly select up to 100 associated registered light/switch entities across zones. Suggest same-area lights; switches require explicit selection. Optional weather source follows existing single-source auto selection.
- CS-FR-003: Freeze selected identities, per-zone light associations, timezone, start/end and optional reference temperature sensor per zone. Never infer occupancy from lights. Reject duplicate, disabled, wrong-domain or missing selections server-side.
- CS-FR-004: Sample HVAC mode/power/settings and selected lights at minute cadence; collect current/target/range, reference and outdoor temperatures hourly, preserving units, provenance and unavailable states. On means enabled mode, not compressor runtime.
- CS-FR-005: Persist, resume with explicit unknown gaps, stop at duration or early stop, and expose saved studies with status, report, JSON export and PDF/print. Reports are available during collection and after completion. No plan-agreement scores or fabricated planned-use bands in a study.
- CS-FR-006: Reuse active-first On-minute ranking and combined hourly table with observed light bands; include reference series and paired thermostat-minus-reference differences with sample count. Describe these as reported differences, not certified calibration offsets. Without a reference, no sensor-offset claim is made.
- CS-FR-007: Allow an optional bounded study note describing intended use/comfort; preserve/export it as user-reported context, never measured occupancy. Ongoing structured comfort questionnaires remain future work.
- CS-FR-008: Study and plan observation coexist without ownership or actuation; one active standalone study at a time to bound collection. Retain existing maximum 20 runs/90-day completed retention.

## Nonfunctional requirements
- CS-NFR-001: Zero device, automation, thermostat-setting, registry or calendar service calls for studies. Admin-only APIs; no outbound data delivery. Private records remain in HA; repository fixtures are fictional.
- CS-NFR-002: Durable atomic/checksummed persistence, idempotent start retries and fail-closed storage errors reuse the observer. Restart/late samples, renamed identities and missing sources remain explicit. No backfilling temperatures or inferring Off during gaps. Maximum 48h/49 hourly slots, 100 zones, 100 unique lights, 20,000 change records and existing store-size bound.
- CS-NFR-003: All setup/status/report strings available in English/Hebrew with RTL, keyboard-labelled controls and accessible table alternatives. UTC arithmetic with configured HA timezone display; elapsed duration remains correct across DST.
- CS-NFR-004: Older plan observations remain readable and unchanged. Study reports distinguish scheduled end, actual stop and incomplete evidence. No timers or notifications scheduled outside the existing minute observer.

## Acceptance
A1 Start without any household/calendar configuration; empty/invalid/overlong selection rejected.
A2 Capture selected zones, lights, reference and weather with no service calls; unselected entities excluded.
A3 Duplicate retry returns same run; changed payload conflicts. Restart gaps unknown; automatic completion and early stop persist and export.
A4 Report shows active ranking, observed lights and reference differences; no plan compliance/occupancy/calibration claim.
A5 EN/HE rendering and print layout are reviewed; live deployment and real 48-hour study validation recorded separately.
