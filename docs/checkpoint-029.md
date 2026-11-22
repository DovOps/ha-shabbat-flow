# Checkpoint 029 — nap feedback and HVAC/fan rehearsal (0.22.0)

New duration-based naps fit within the selected day with an adjacent explanation. Invalid explicit clock windows show an adjacent accessible error. Permanent defaults and existing naps are unchanged.

Immediate rehearsal supports mapped HVAC power and room fans, explicit active mode/speed capture, settings preservation checks, and context-qualified restore. No climate temperature/fan-mode setters or guessed mode when Off. Native fans preserve speed/preset; switch-backed fans are binary. Fan assignments alone do not invent timing. Ownership checks now recognize climate/fan settings services. Scheduled execution remains lighting-only.

Deployment and read-only UI verification completed. Owner hardware acceptance remains pending; no physical tests were run during installation.

Automated checks: 169 HA tests on both 2026.8.2 and 2026.11.2, 94 core and 68 JavaScript tests pass. Generated assets, hygiene and whitespace checks pass. Both website locales build; link checks pass. Fictional EN/HE nap creation, boundary explanation and editable times visually verified. Package SHA-256: `9d829b80997de6544c96922be3860a601d5e977c582e52bcfc8a01bf6120eac2`.

Installation verified: 72 package files byte-matched, all three saved-data files preserved, integration/storage backup created on host, and one HA restart. No device rehearsal or scheduled control was activated. The versioned 0.22.0 UI loaded with all saved rooms ready. Adding a duration-based nap succeeded with an adjacent boundary-shortening explanation. Read-only rehearsal showed the planned HVAC On event and correctly required an active-mode baseline while the unit was Off. No draft test edits were saved. Real power/settings preservation and restore remain owner-supervised acceptance tasks.
