# Feature 013 — Public documentation and brochure website

## Functional requirements
- WEB-FR-001: Provide a Docusaurus brochure homepage explaining room-based Shabbat/Yom Tov planning, multi-day calendar anchors, lighting/HVAC schedule previews, observe mode, climate studies, optional notifications and pre-candle reminders. Clearly distinguish implemented capabilities from future device execution.
- WEB-FR-002: Publish installation/onboarding, capability/status, contribution and specification navigation. Generate the technical reference from canonical repository specs at build time; never maintain a second editable specification copy. Include the current integration version from its manifest.
- WEB-FR-003: Offer English and Hebrew homepage, navigation and getting-started guides, with RTL. Canonical technical requirements remain English and are explicitly identified as such in Hebrew views.
- WEB-FR-004: Support a loopback local preview and project-site deployment at `https://dovops.github.io/ha-shabbat-flow/`, including locale routes, assets and deep links under that base path.
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
