# Installable sample implementation plan
1. Add config-entry lifecycle, optional calendar entity options, authenticated preview/read endpoints and an HA custom panel.
2. Bridge only allowlisted planner API requests from the embedded UI through the authenticated HA frontend; do not pass tokens or the hass object to the inner application.
3. Replace timestamp text fields with date/time controls, preserving IANA timezone/DST validation and second precision. Offer explicit use of configured source values; never auto-overwrite a draft.
4. Build a self-contained package from reviewed source assets/compiler; check generated files and produce a checksummed ZIP.
5. Test against an isolated pinned HA installation and run existing checks. Document installation, upgrade, rollback, removal and known limits.
6. Commit/push checkpoint and merge to main under existing authorization. Do not install or restart household HA.

Validate manifest/constant/static-route equality before any archive build. Exercise mismatch rejection and compare the actual registered HA panel URL with the manifest in lifecycle tests.
