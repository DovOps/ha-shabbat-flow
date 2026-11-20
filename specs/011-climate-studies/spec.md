# Feature 011 — Standalone climate studies

## Scope and clarification
Administrators can manually observe ordinary household climate use without calendar data, a complete room setup, a schedule or automation. This is evidence for comfort/setpoint review, not automatic thermostat calibration. Start immediately for 1–48 whole hours (default 24); stop early if needed. Scheduled starts and sending summaries are deferred. No new dependencies.

## Functional requirements
- CS-FR-001: Offer Climate Study directly from house setup; no Shabbat plan or Jewish Calendar is required.
- CS-FR-002: Select 1–100 enabled registered climate zones and 1–48 hours. Explicitly select up to 100 associated registered light/switch entities across zones. Suggest same-area lights and switches; both require explicit selection. Optional weather source follows existing single-source auto selection.
- CS-FR-003: Freeze selected identities, per-zone light/switch activity-signal associations, timezone, start/end and optional reference temperature sensor per zone. Never infer occupancy from lights. Reject duplicate, disabled, wrong-domain or missing selections server-side.
- CS-FR-004: Sample HVAC mode/power/settings and selected lights and switches at minute cadence; collect current/target/range, reference and outdoor temperatures hourly, preserving units, provenance and unavailable states. On means enabled mode, not compressor runtime.
- CS-FR-005: Persist, resume with explicit unknown gaps, stop at duration or early stop, and expose saved studies with status, report, JSON export and PDF/print. Reports are available during collection and after completion. No plan-agreement scores or fabricated planned-use bands in a study.
- CS-FR-006: Reuse active-first On-minute ranking and combined hourly table with observed light bands; include reference series and paired thermostat-minus-reference differences with sample count. Describe these as reported differences, not certified calibration offsets. Without a reference, no sensor-offset claim is made.
- CS-FR-007: Allow an optional bounded study note describing intended use/comfort; preserve/export it as user-reported context, never measured occupancy. Ongoing structured comfort questionnaires remain future work.
- CS-FR-008: Study and plan observation coexist without ownership or actuation; one active standalone study at a time to bound collection. Retain existing maximum 20 runs/90-day completed retention.

## Nonfunctional requirements
- CS-NFR-001: Zero device, automation, thermostat-setting, registry or calendar service calls for studies. Admin-only APIs; no outbound data delivery. Private records remain in HA; repository fixtures are fictional.
- CS-NFR-002: Durable atomic/checksummed persistence, idempotent start retries and fail-closed storage errors reuse the observer. Restart/late samples, renamed identities and missing sources remain explicit. No backfilling temperatures or inferring Off during gaps. Maximum 48h/49 hourly slots, 100 zones, 100 unique lights/switches, 20,000 change records and existing store-size bound.
- CS-NFR-003: All setup/status/report strings available in English/Hebrew with RTL, keyboard-labelled controls and accessible table alternatives. UTC arithmetic with configured HA timezone display; elapsed duration remains correct across DST.
- CS-NFR-004: Older plan observations remain readable and unchanged. Study reports distinguish scheduled end, actual stop and incomplete evidence. No timers or notifications scheduled outside the existing minute observer.

## Acceptance
A1 Start without any household/calendar configuration; empty/invalid/overlong selection rejected.
A2 Capture selected zones, lights, reference and weather with no service calls; unselected entities excluded.
A3 Duplicate retry returns same run; changed payload conflicts. Restart gaps unknown; automatic completion and early stop persist and export.
A4 Report shows active ranking, observed lights and reference differences; no plan compliance/occupancy/calibration claim.
A5 EN/HE rendering and print layout are reviewed; live deployment and real 48-hour study validation recorded separately.

## Room activity signals — 0.14.0 follow-up
- CS-FR-009: Allow any enabled registered light or switch associated with a selected zone to be explicitly selected as a room activity signal, including non-lighting switches and switches assigned through their device area. Suggest same-room entities and allow explicit cross-room association. Display each selected signal's observed On/Off/Unknown timeline alongside that zone's temperatures, identifying switches separately from lights in HTML/PDF and retaining identity/state changes in JSON. No automatic device selection or actuation.
- CS-NFR-005: Signal activity is not confirmed occupancy or manual interaction. Both On and Off changes can be useful evidence, including brief visits; persistent On may be convenience or an automation. Do not infer a person, causal attribution, or a fixed occupancy window. Missing/restart periods remain Unknown and one-minute sampling can miss brief episodes. Preserve the existing `lights`/`study_lights` wire keys for compatibility; they contain selected light and switch activity signals.

### Bulk signal selection
- CS-FR-010: Provide Select all in this room and Clear all in this room buttons for each selected zone's activity signals. Affect same-area lights and switches only; preserve explicitly selected other-area signals. Entities with no area do not form an implicit room. Never start observation or control devices through bulk selection.
- CS-NFR-006: Bulk controls have English/Hebrew labels, native keyboard activation and disabled states when no room candidates exist. Update checkboxes in place, retaining focus, weather source, references, duration, notes and saved-run selection. Existing 100-unique-signal server validation remains authoritative.

Feature 012 adds optional explicitly enabled lifecycle SMS/app-push and secure report links. Default studies remain silent and read-only with no device/automation actions; notification settings are separate and excluded from exports. Scheduled studies and automatic calibration remain deferred.

## Responsive study selection
- CS-FR-011: Zone selection updates only that zone, preserving other selections, references, weather, notes, duration and saved-run controls. Load cross-room signal choices only when expanded, in explicit batches of at most 50. Bulk same-room selection remains independent of cross-room pagination.
- CS-NFR-007: Verify selection with 100 zones and 2,000 candidate signals. A zone toggle must not rebuild sibling zone cards or reinitialize observation controls; collapsed cross-room lists create no signal controls. Icon rendering is cached by icon name, bounded on missing graphics, and cannot require a study to start. Verify focus and values remain stable in EN/HE.
