# Build from the requirements

ShabbatFlow uses a specification-driven workflow: requirements, implementation plan, tasks, analysis, implementation and verification. Keep functional and nonfunctional requirements updated in the same change as the code.

The public repository must contain reusable examples only. Keep real family details, entity IDs, household histories, credentials and installation screenshots outside it. Use fictional fixtures and the original project branding. Do not claim Home Assistant endorsement or copy other integrations' designs without review.

Read [contributor instructions](https://github.com/DovOps/ha-shabbat-flow/blob/main/AGENTS.md), the [constitution](https://github.com/DovOps/ha-shabbat-flow/blob/main/.specify/memory/constitution.md), and [dependency decisions](reference/docs/dependencies.md). Contributions use DCO sign-off (`git commit -s`).

## Keep this site current

The brochure and guides live in `website/src` and `website/content`. Technical references are generated from `specs/` and selected maintained `docs/` sources. Edit those canonical files, not generated output. The build reads the integration version directly from its manifest.

From the repository root:

```sh
cd website
npm ci
npm run build
npm run check
npm run serve
```

The preview is at `http://localhost:3000/ha-shabbat-flow/`; Hebrew is at `/ha-shabbat-flow/he/`. Use `npm start` for English development with hot reload, or `npm start -- --locale he` for Hebrew. Re-run content preparation after editing canonical specifications.

Pull requests build both locales. Once Pages is enabled, pushes to `main` publish the tested website through GitHub Actions. The repository's website maintenance guide documents the one-time Pages setup.
