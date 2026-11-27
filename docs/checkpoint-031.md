# Checkpoint 031 — rehearsal selection and remembered power

0.22.1 adds explicit native remembered-settings power tests, while retaining captured/current preservation as the default. No temperature, mode, speed or preset arguments are sent in remembered mode. Observed settings are recorded; later settings/context changes block restore. Unsupported native power capabilities remain excluded. Explicit settings editing remains future scope.

Review offers scoped Select all eligible devices, clear selection, a selected count and collapsed exclusions retaining capture/reasons. Apply requires nonempty bounded selection, valid per-device notes and supervision, with adjacent explanations. Prominent planner blocker callouts identify missing mappings and affected rooms. EN/HE strings and specs updated.

Validation: 94 core, 70 web and 32 rehearsal tests on each supported HA version pass; repository hygiene, generated assets and whitespace checks pass. Installed 76 files byte-verified with backup, three saved stores preserved. One backend restart completed. Installed 0.22.1 UI verified: all 20 saved rooms ready, remembered-policy review makes an Off HVAC target selectable without capture, bulk selection excludes blocked rows, count/prerequisite updates and disabled Apply verified. EN/HE policy labels checked; no rehearsal applied. No device controls or scheduled plans activated.

Additional startup/API regression: 88 integration tests pass on HA 2026.11.2.
