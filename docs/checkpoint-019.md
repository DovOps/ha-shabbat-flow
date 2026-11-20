# Checkpoint 019 — relevant existing automations and public website

## Implemented
- Filter dated forecasts to scheduled clock/sun and registry-identified Jewish Calendar sources. Reactive switch synchronization stays out of schedule diagnostics; fingerprints and excluded-source ownership uncertainty remain available.
- Resolve bounded issur transitions and state conditions only under a provider-sourced continuous-period snapshot with a single provider. Multi-day intermediate candles do not create false on/off transitions. Unsupported calendar events/templates remain diagnostic.
- Friendly automation/device names, device icons and Existing Automation label. Group same automation/instant/action without changing raw per-device events. Distinct action states and times stay separate.
- Unresolved details collapsed by default. Print excludes detailed diagnostics and technical identifiers, retaining grouped events and a short count/limitations note.
- Website canonical origin is https://dovops.io with /ha-shabbat-flow/ base path. Owner made repository public and authorized Pages publication. Existing Pages configuration already uses workflow builds and inherits the account domain; no project CNAME or DNS change is needed.

## Verification
- Python core: 76 passed; browser logic: 52 passed. HA integration: 111 passed on 2026.11.2 and 111 on 2026.8.2.
- Covered reactive/mixed trigger filtering, 23:00 timer, continuous-calendar on/off, conditional eligibility, source/device names, icons, grouping and diagnostic PDF omission.
- Local EN/HE visual verification used a fictional two-device exterior timer. Diagnostic disclosure is initially collapsed; identifiers are secondary. No household screenshot was copied into the repository.
- Both locale website production builds and project-path checks passed.

## Rollout
HA 0.16.1 package prepared, not installed; no device/automation changes or HA restart. Public site deployment is authorized; completion is verified separately through GitHub Actions and public HTTP checks.
