# ShabbatFlow contributor instructions

- Read `.specify/memory/constitution.md` and the active `specs/` feature before edits.
- Read `docs/dependencies.md`: third-party source, design and dependencies require the owner's review of an exact proposal. Research references are not adopted dependencies.
- Follow specification → clarification → plan → tasks → analysis → implementation → verification. Update requirements and tests together.
- Never read/import sibling household backups, credentials, logs, inventory or personal history into this repository. Use only fictional fixtures. No identifying household names, addresses, document IDs, home locations or workstation paths in tracked files.
- No Home Assistant device calls, production installation or automation modifications without a separately reviewed authorization. Preview code has no execution adapter.
- English and Hebrew are first-class. Translate every user-facing string and validate RTL and keyboard behavior. Stable machine codes remain language-independent.
- Do not infer occupancy, identity or religious affiliation from device use.
- Commit or push only within the user’s authorization. When the user authorizes ongoing checkpoint commits, do not request confirmation for each routine commit. A commit authorization alone does not authorize a push. When later committing, use the configured GitHub alias/noreply identity; never substitute a personal email.
- Run `PYTHONPATH=src python3 -m unittest discover -s tests -v`, `node --test tests/web.test.mjs`, and `python3 scripts/check_repository.py` before proposing a checkpoint.
- Document actual verification and remaining limitations; do not mark HA deployment or future roadmap features complete.
