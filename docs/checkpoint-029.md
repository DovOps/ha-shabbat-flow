# Checkpoint 029 — nap feedback and HVAC/fan rehearsal (0.22.0)

New duration-based naps fit within the selected day with an adjacent explanation. Invalid explicit clock windows show an adjacent accessible error. Permanent defaults and existing naps are unchanged.

Immediate rehearsal supports mapped HVAC power and room fans, explicit active mode/speed capture, settings preservation checks, and context-qualified restore. No climate temperature/fan-mode setters or guessed mode when Off. Native fans preserve speed/preset; switch-backed fans are binary. Fan assignments alone do not invent timing. Ownership checks now recognize climate/fan settings services. Scheduled execution remains lighting-only.

Final verification/deployment evidence pending. Owner hardware acceptance remains pending; no physical tests are run during installation.

Automated checks: 169 HA tests on both 2026.8.2 and 2026.11.2, 94 core and 68 JavaScript tests pass. Generated assets, hygiene and whitespace checks pass. Both website locales build; link checks pass. Fictional EN/HE nap creation, boundary explanation and editable times visually verified. Package SHA-256: `9d829b80997de6544c96922be3860a601d5e977c582e52bcfc8a01bf6120eac2`.
