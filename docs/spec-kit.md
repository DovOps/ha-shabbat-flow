# Spec Kit workflow and provenance

Official upstream: https://github.com/github/spec-kit

Pinned source snapshot: `e210504aa09c9273a38bba665b12b8088468c96f`.
Unmodified templates and Bash scripts are vendored under `.specify/`; license is in `docs/vendor/spec-kit-LICENSE`.

The installed 0.1.13 CLI could not initialize against the current upstream release (no matching legacy template archive). This bootstrap therefore used the official source templates and `create-new-feature.sh` directly. It is a source-based Spec Kit bootstrap, not a claim that a newer CLI or Codex slash commands were installed. No global agent configuration was changed.

Workflow for each feature:
1. Read the constitution.
2. Write `spec.md` using the upstream user-story/requirements/success-criteria structure.
3. Record clarifications, open decisions and reuse research.
4. Write `plan.md`, `data-model.md`, contracts and quickstart.
5. Write `tasks.md` with test coverage and dependencies.
6. Cross-check traceability in `analysis.md` before implementation.
7. Implement tasks, run checks and record evidence in `verification.md`.
8. Review the checkpoint before commit/push or deployment.

Current feature: `specs/001-preview-planner`. Use `bash .specify/scripts/bash/check-prerequisites.sh --json` to inspect it. Future full CLI installation should be pinned and reviewed independently; do not overwrite local specifications.
