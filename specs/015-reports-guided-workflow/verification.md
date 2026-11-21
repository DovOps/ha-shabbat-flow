# Verification — 0.18.0

- UX-FR-001–003: Reports archive filters and empty states; planner command IDs remain unique and before the form; EN/HE browser checks verify top commands, optional sections and report links. Narrow planner viewport checked for horizontal overflow (375px client/scroll width at 390px viewport).
- RP-FR-001–002: Pure projection tests verify known-only agreement denominator, unknown-only null score, climate-score suppression, partial status, alias deduplication and unchanged source run. Room totals are device-minutes, not elapsed period duration or execution success.
- RP-FR-003–005 / RP-NFR-002–003: HA tests cover validation, no service calls, immutable bundle, stale revision rejection, review revision/history, restart reload, clearing and write failure without memory success. Admin auth remains enforced. Compact archive excludes inventory and full histories.
- UX-NFR-001 / RP-NFR-001: 62 JS tests pass, including EN/HE key parity, report filters, export shape and unique command locations. Full reports load on demand. Browser fixture exercises save and report re-render. Shared PDF renderer includes saved feedback and performance; print CSS hides navigation and editor.
- Regression: 91 Python core tests, 116 HA tests on each supported HA version (2026.8.2/2026.11.2); dependency deprecation warnings remain. Generated asset parity and repository hygiene passed.

Not live-validated: physical-device execution, causal impact of proposed changes, multi-person feedback, automatic trend/proposal workflow. Full mobile native print dialog/device acceptance remains a user check. No production study starts or feedback writes are needed to verify installation.

- Brochure: both locales built; 156 pages and 7,072 relative links/assets passed. Four EN/HE gallery screenshots use fictional fixtures.
