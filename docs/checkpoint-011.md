# Preview 0.11.0 — circulation and independent meal HVAC

US13 adds independent dinner/lunch lighting and HVAC bindings, optional recreation HVAC, always-on access main lights, explicit main-light Off at a night transition, a derived end-of-entertaining anchor, bounded morning main-light windows, and explicit existing-automation ownership of the morning night-light release. English/Hebrew controls and setup tips are included. No household identifiers or historical data are embedded in the package.

Old combined meal settings inherit their old HVAC choices until explicitly edited. Existing exports remain valid. New workspaces capture changed bindings; saved drafts are never rewritten. Continuous historical HVAC operation is evidence only, never an inferred requirement to leave it running.

Verification: 76 Python tests, 39 Node tests, and 82 HA tests on each of 2026.8.2 and 2026.11.2 passed. New cases cover independent daytime power-only HVAC, always-on lighting ignoring daylight breaks, post-observance policy, per-day entertaining anchors and fallback, 1–3-day circulation windows, away behavior, external release with repeated nightly On, explicit main Off and UI validation parity. Existing timezone/DST and migration regression tests also passed. Generated bundle, diff and repository hygiene checks passed.

The package is built locally. Browser interaction/visual QA for these new controls has not been performed, and 0.11.0 has not been deployed to HA. Existing-automation release deliberately emits no Off event; its warning explains that the preview/chart retains the last planned On and does not forecast the external automation. No execution adapter or existing-automation overlay is added.
