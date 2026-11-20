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
HA 0.16.1 was subsequently installed with explicit owner authorization; see deployment evidence below. Public site deployment is authorized; completion is verified separately through GitHub Actions and public HTTP checks.

## Public deployment completed
GitHub website run 44698117332 and checks run 44698117317 succeeded for main merge 751494f. PAGES_ENABLED is true. Verified HTTP 200 and expected page titles at the public HTTPS homepage, Hebrew homepage, EN/HE galleries and room-options guide. No DNS or CNAME change was made.

## HA deployment completed
Authorized upgrade to 0.16.1 completed with an on-host integration/storage backup and one HA restart. All 51 package files matched the archive; Python source parsed successfully and both saved storage files were byte-identical during installation. The live panel loaded versioned 0.16.1 assets, retained saved room setup and notification preferences, and displayed the renamed navigation and dependency status tiles. Native HA icon elements were present in room summaries. No device control was enabled, no study was started and no notification settings were changed. Real-plan forecast review and completed-study validation remain pending.
