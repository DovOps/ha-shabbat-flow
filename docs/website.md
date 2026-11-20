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

The site target is `https://dovops.github.io/ha-shabbat-flow/`. PRs build both languages without deploying. Every main push builds, checks and publishes once the repository is public and the enablement variable is set. Until then, builds produce a Pages artifact and skip publication. To stop future deployments, unset `PAGES_ENABLED`; this does not remove an already published site. Use Pages settings separately to unpublish.

No PAT, SSH key or HA credential is needed. PR jobs have contents-read permission; the deployment job uses only Pages-write and OIDC. The site has no HA connection, analytics or public household reports.

Reference: [Docusaurus deployment](https://docusaurus.io/docs/deployment), [GitHub publishing configuration](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Dependency maintenance

Website tooling is pinned in its own lockfile. Overrides for `tinypool` 2.2.0, `serialize-javascript` 7.1.4 and `uuid` 11.1.1 select patched transitive versions compatible with the verified build. Re-evaluate overrides when upgrading Docusaurus; run `npm audit`, both locale builds and the output checks. They add no HA runtime dependency.
