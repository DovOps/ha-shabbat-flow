# Website maintenance and publication

The Docusaurus site lives in `website/`. It is a static brochure/documentation site, separate from the HA integration. EN/HE product content is authored; the English technical reference is generated from canonical `specs/` and an allowlist of maintained `docs/` files. The manifest supplies the displayed integration version. Never put private deployment screenshots, household data or credentials into website assets.

## Local review

Use Node 22 (20+ supported) and npm:

```sh
cd website
npm ci
npm run build
npm run check
npm run serve
```

Open `http://localhost:3000/ha-shabbat-flow/` or its `he/` path. The production preview serves both locales. `npm start` provides English hot reload; `npm start -- --locale he` provides Hebrew. Re-run `npm run prepare-content` after canonical source edits. Generated files and built assets are ignored; commit source and lockfile only.

`npm run check` verifies every canonical spec is published in both locale trees, correct version metadata and all project-relative links/assets. Docusaurus also fails broken links during builds. Keep website copy consistent with actual implementation status, without claiming official HA verification before it is established.

## One-time GitHub Pages setup

The owner controls when the repository becomes public. This change does not alter visibility or enable Pages.

When ready:

1. Make the repository public after your repository/history review.
2. In repository **Settings → Pages → Build and deployment**, select **GitHub Actions**.
3. In **Settings → Secrets and variables → Actions → Variables**, add repository variable `PAGES_ENABLED` with value `true`.
4. Run the **website** workflow manually on `main`, or merge a change into `main`.

The site target is `https://dovops.io/ha-shabbat-flow/`. PRs build both languages without deploying. Every main push builds, checks and publishes once the repository is public and the enablement variable is set. Until then, builds produce a Pages artifact and skip publication. To stop future deployments, unset `PAGES_ENABLED`; this does not remove an already published site. Use Pages settings separately to unpublish.

No PAT, SSH key or HA credential is needed. PR jobs have contents-read permission; the deployment job uses only Pages-write and OIDC. The site has no HA connection, analytics or public household reports.

Reference: [Docusaurus deployment](https://docusaurus.io/docs/deployment), [GitHub publishing configuration](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Dependency maintenance

Website tooling is pinned in its own lockfile. Overrides for `tinypool` 2.2.0, `serialize-javascript` 7.1.4 and `uuid` 11.1.1 select patched transitive versions compatible with the verified build. Re-evaluate overrides when upgrading Docusaurus; run `npm audit`, both locale builds and the output checks. They add no HA runtime dependency.

## Developer guide and screenshot gallery

The EN/HE developer guide is `website/content/*/contributing.md`; README and root AGENTS.md point contributors to it. It recommends agent-assisted spec-driven work without requiring a particular agent or claiming automatic instruction loading.

The gallery page uses actual interface captures with fictional data only. See `website/static/img/gallery/README.md` for capture versions and provenance. Recheck every replacement for private content, update both locales and preserve the distinction between actual interface screens and real household evidence. The approved logo remains unchanged; visitor-facing product naming is Shabbat Flow.

## Current public deployment
Live at https://dovops.io/ha-shabbat-flow/ with Hebrew at /ha-shabbat-flow/he/. The project inherits the account's custom domain. Pages uses GitHub Actions and PAGES_ENABLED=true; merges to main now publish automatically. Keep the project baseUrl and do not add a conflicting project CNAME. Initial public deployment and route verification are recorded in checkpoint 019.

0.18.0 gallery additions: reports-en/he.png and review-en/he.png were captured from the real UI through the loopback-only `scripts/gallery_preview.py` fixture. The report IDs, dates, Room A, sample agreement totals and cleanup note are fictional. No HA household export was used. Brochure copy and both setup guides explain Reports, the owner-review loop and observe-only limits.
