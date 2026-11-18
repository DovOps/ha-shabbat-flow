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
