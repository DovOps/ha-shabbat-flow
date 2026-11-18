# PDF export implementation checkpoint

## Plan
Use an isolated report renderer and dedicated print CSS alongside the existing JSON export. Reuse the visible complete preview's warnings, event descriptions and action badges. Add dated plan context, logo, meals, room uses and availability. Use browser printing to retain native Hebrew shaping and avoid new dependencies.

## Tasks
- [x] Specify MD-FR-011–012 and MD-NFR-005.
- [x] Implement localized export controls, complete-preview gate and invalidation after edits.
- [x] Build branded report with repeated table headers and event-row pagination rules.
- [x] Add EN/HE multi-day report regression coverage and build installable 0.8.1.
- [ ] Visually inspect actual English/Hebrew multi-page PDF output.
- [ ] Install and verify in HA after visual verification.

## Analysis and verification
No new runtime dependency, external service, device control or plan mutation. JSON remains available. Native HA WebViews may lack a print UI; guidance directs the owner to open the planner in a browser and select Save as PDF. This is a print-to-PDF flow, not a direct binary PDF download.

65 Python and 32 Node tests passed. Report tests verify three dated sections, year/timezone, complete event rows, retained warnings, no raw configuration, unchanged inputs and incomplete-preview refusal in both languages. Generated package, repository hygiene and whitespace checks passed. Browser visual verification was blocked by a saved local-origin permission. Do not claim visual pagination or native-app compatibility as verified; 0.8.0 remains installed.

## Calendar cards and lighting map plan
Use optional bounded presentation metadata on dated calendar segments and loads. Exclude it from semantic digests. Read all-day summaries from the existing accepted Jewish Calendar event feed; do not query a current-day sensor for future metadata. Render one local calendar day per chart, with eight-light chunks for pagination and a lane per load. Derive intervals from compiled state intentions, carrying state across dates. Keep unknown intervals hatched and ignore track-only events. Preserve the event list for exact details.

- [x] Specify MD-FR-013–015 and MD-NFR-006.
- [x] Implement metadata validation and read-only provider mapping.
- [x] Implement shared HTML/PDF day cards and lighting map.
- [x] Add semantic-digest, metadata and DST/carryover regression tests.
- [x] Install 0.9.0 and verify the live interface.

## 0.9.0 verification
66 core Python tests, 33 web tests and 72 HA tests on each supported HA version passed. Coverage includes three-day PDF structure, EN/HE labels, optional provider metadata, strict length/type bounds, unchanged semantic digest/events, unknown initial state, overnight continuation, track-only exclusion, absent final Off and 23/25-hour DST axes. Package consistency and repository hygiene passed.

The user confirmed the previous PDF export worked in the local browser. Actual new multi-page print pagination remains subject to browser print settings; installed visual verification is recorded separately below.

### Installed verification — 2026-11-18
- Verified archive SHA-256 `2571296e828eb202f4d9066aa39df2c27f36e4d2f1eb9608dd81029fc8c54126`, all 32 extracted files and Python syntax. Integration and household Store backups remain inside HA. Stored setup was byte-for-byte unchanged during installation. One Core restart loaded 0.9.0.
- Opened a new workspace and observed actual dated Hebrew-date and weekly-portion summaries from Jewish Calendar. Generated an unsaved test preview with home availability and meals, without saving household settings or browser drafts. Visually inspected both local-day charts, main/night changeover and daylight-break bars against the event list. Existing unclassified areas remain explicit rather than inferred from their names.
- Live Export PDF / Print control is available. Automated interaction with Chrome's print flow timed out; actual new PDF pagination was not visually verified in this pass. The shared report renderer and multi-day structure are regression-tested. Screenshots remain outside the repository.
- GitHub CI run `44289419389` passed for implementation `8bfda60`. No device calls or automation changes.
