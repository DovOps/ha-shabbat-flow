# Developer guide: coding agents and specifications

Shabbat Flow uses a specification-driven workflow: requirements, implementation plan, tasks, analysis, implementation and verification. Keep functional and nonfunctional requirements updated in the same change as the code.

The public repository must contain reusable examples only. Keep real family details, entity IDs, household histories, credentials and installation screenshots outside it. Use fictional fixtures and the original project branding. Do not claim Home Assistant endorsement or copy other integrations' designs without review.

Read [contributor instructions](https://github.com/DovOps/ha-shabbat-flow/blob/main/AGENTS.md), the [constitution](https://github.com/DovOps/ha-shabbat-flow/blob/main/.specify/memory/constitution.md), and [dependency decisions](reference/docs/dependencies.md). Contributions use DCO sign-off (`git commit -s`).

## Recommended: develop with a coding agent

This project is designed for **LLM/coding-agent-assisted, specification-driven development**. An agent can read the requirements, propose a bounded change, implement it and run checks while you review the decisions. Human-only contributions are equally welcome; the same workflow applies.

**Start at the repository root with `AGENTS.md`.** It is the agent's entry point for the development workflow, contribution boundaries, required checks and specification maintenance. Do not assume your chosen tool loaded it: explicitly ask the agent to read it, then the constitution and the relevant feature under `specs/`.

### From request to reviewable change

1. Read `AGENTS.md`, `.specify/memory/constitution.md`, `docs/dependencies.md` and the relevant feature specification.
2. Clarify the requested behavior. Update functional requirements (FRs), nonfunctional requirements (NFRs), acceptance criteria and known limitations **before implementation**.
3. Update the implementation plan and tasks; cross-check dependencies and requirement traceability in the analysis.
4. Implement a small, reviewable increment with fictional fixtures. Maintain English/Hebrew behavior and RTL where the UI changes.
5. Run the required repository checks and checks appropriate to the change. Record what actually passed; separate implementation, installation and live validation.
6. Update requirement status and the roadmap. Review the diff, especially for household data, before any authorized signed-off commit or push. Deployment and device control require separate authorization.

The repository follows GitHub Spec Kit conventions through vendored templates and scripts. This does not mean an agent-specific slash-command installation is required or already available. See [Spec Kit workflow and provenance](https://github.com/DovOps/ha-shabbat-flow/blob/main/docs/spec-kit.md).

### A starter prompt you can copy

```text
Work from the repository root. Read AGENTS.md, the constitution,
dependency decisions and the specs relevant to this request:
[describe the change].

First update the FRs, NFRs, acceptance criteria, plan and tasks.
Identify open decisions before implementing a small, reviewable increment.
Use fictional fixtures; do not import household data or credentials.
Keep multilingual behavior (English/Hebrew defaults) and documentation current.
Run the required checks and report evidence and remaining limitations.
Do not deploy, control devices, or commit/push without my authorization.
```

An agent's output is a contribution to review, not approval or proof of correctness. The repository specifications—not chat history alone—must retain the decisions needed by the next contributor or agent.

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
