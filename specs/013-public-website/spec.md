# Feature 013 — Public documentation and brochure website

## Functional requirements
- WEB-FR-001: Provide a Docusaurus brochure homepage explaining room-based Shabbat/Yom Tov planning, multi-day calendar anchors, lighting/HVAC schedule previews, observe mode, climate studies, optional notifications and pre-candle reminders. Clearly distinguish implemented capabilities from future device execution.
- WEB-FR-002: Publish installation/onboarding, capability/status, contribution and specification navigation. Generate the technical reference from canonical repository specs at build time; never maintain a second editable specification copy. Include the current integration version from its manifest.
- WEB-FR-003: Offer English and Hebrew homepage, navigation and getting-started guides, with RTL. Canonical technical requirements remain English and are explicitly identified as such in Hebrew views.
- WEB-FR-004: Support a loopback local preview and project-site deployment at `https://dovops.io/ha-shabbat-flow/`, including locale routes, assets and deep links under that base path.
- WEB-FR-005: GitHub Actions builds both locales for pull requests and publishes GitHub Pages on pushes/merges to main or manual dispatch once the owner enables Pages. Do not change repository visibility. Preserve a working local preview for owner review.
- WEB-FR-006: Use the approved original ShabbatFlow logo and accurate custom-integration positioning. Do not claim official HA verification, endorsement, HACS inclusion or production execution before evidence and an explicit status update. Readiness and validation limits are visible.

## Nonfunctional requirements
- WEB-NFR-001: Static public output contains no household configuration/history, private screenshots, tokens, phone numbers or real room/entity mappings. Use fictional illustrative schedules. No HA connection, analytics or forms transmitting visitor data.
- WEB-NFR-002: Website-only pinned npm dependencies and lockfile; no change to HA runtime dependencies. Build reproducibly with npm ci. Fail on broken internal links; check generated spec coverage and project base paths.
- WEB-NFR-003: Responsive at mobile/desktop widths, visible keyboard focus, semantic headings, text labels for timeline states, reduced-motion support, and English/Hebrew language switching. No color-only state meaning.
- WEB-NFR-004: CI uses read-only permissions for PR builds and Pages/OIDC permissions only for deployment; no PAT or SSH deployment key. Deployment is gated by explicit Pages enablement, separate from repo visibility.

## Acceptance
A1 Fresh clone: npm ci/build succeeds for both locales; each canonical spec is reachable in the site reference.
A2 Local root, guide, technical specification, mobile menu and Hebrew routes render correctly under the repository base path.
A3 Updating a canonical spec/version changes generated site content on the next build.
A4 PR builds do not deploy; main deployment workflow is ready, without changing repository visibility or enabling a public site before the owner is ready.
A5 Homepage makes clear that device execution remains future scope and official HA verification is unconfirmed.

## Developer onboarding, gallery and naming
- WEB-FR-007: Make the recommended LLM/coding-agent-assisted, spec-driven workflow prominent in the README and EN/HE developer guide. Identify root AGENTS.md as the entry point; require reading the constitution and relevant specs, updating FR/NFR/acceptance/plan/tasks before coding, recording verification/status, and human review. Include a copyable tool-neutral starter prompt. Human-only contributions remain welcome; do not imply automatic instruction discovery or installed agent slash commands.
- WEB-FR-008: Provide a gallery of actual application/rendered-report captures using fictional data, with EN/HE captions, accessible descriptions, full-size links and capture-version/provenance notes. Clearly distinguish real interface screenshots from live household evidence and illustrative homepage graphics. Screens may remain English while visitor-facing explanations are multilingual.
- WEB-FR-009: Present the product as Shabbat Flow, preserving its approved logo and stable repository/domain/URL identifiers. Remove Preview from product naming; retain accurate preview/observation/execution limitations as separate status information. Website navigation must visibly identify its active section and expose gallery/developer-guide links.
- WEB-NFR-005: Review every published image for private names, entities, contact details, URLs and history; use only fictional fixtures. Keep source provenance and capture version adjacent to the gallery implementation. EN/HE navigation, captions, brochure and setup/developer guides are maintained together; canonical technical specs may stay English with an explicit notice.

A6 A new contributor can find AGENTS.md and copy a starter prompt without searching the technical specs. A7 Both locales expose gallery images/captions/full-size links and clear active navigation. Gallery screenshots contain no actual household data and do not claim to show a newer capture version.

## Localized workflow gallery and option guide
- WEB-FR-010: Each locale uses actual interface captures in that language, including room setup, configured daily planning, schedule timeline/event list and observation/climate reporting. Explain synthetic calendar/data and capture version. This supersedes FR-008's English-only screenshot allowance.
- WEB-FR-011: EN/HE user guide documents each lighting preset, night-mode alternative, daylight policy, HVAC choice, bathroom-link window, bedroom applicability and rest timing option with concrete examples. Explain what is changed, what remains independent and when changes are saved.
- WEB-NFR-006: Maintain locale pairs and privacy-reviewed provenance; build checks fail for absent gallery assets. No live household captures. Capture actual local production renderers rather than illustrative mockups.

- WEB-FR-012: Include EN/HE Settings gallery captures from the actual renderer using fictional capabilities, never household notification/contact settings. State prominently that planning and observe mode are available and device control is future functionality; do not imply that an unreleased executor is production-ready.

- WEB-FR-013: Extend the brochure gallery with English/Hebrew production-renderer captures of the home overview, including concurrent scheduled plan observation and active climate study, and Rooms at a glance with Ready, Draft and Needs attention examples. Explain browser-local drafts versus persisted observations and clickable room review. Label statuses/dates as fictional; never publish live household captures.
- WEB-NFR-005: Keep new screenshots paired by locale, inspect legibility and RTL, provide descriptive captions/alt text and capture provenance/version. Use a read-only loopback fixture and no production data, study creation or device control.
