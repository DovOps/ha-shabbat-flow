# Checkpoint 021 — climate temperature defaults and bilingual selection

## Implemented
- Explicit built-in A/C temperature default; optional chooser now means an additional comparison sensor. Native current temperature, target and mode were already collected without a reference, including available readings while Off. No self-comparison or fake zero calibration delta is introduced.
- Checkbox/icon/name rows start together at the left in English and right in Hebrew, including shared room/notification checkbox styles. Mixed-direction names do not move checkboxes into the center.
- Retain zone/activity selections and notes through language changes; keep weather/run choices across observer UI reinitialization. Lazy other-room lists stay unmaterialized after language change. Includes the earlier 0.16.2 cached icon and targeted zone-render fixes.

## Verification
- 76 Python core and 54 JavaScript tests passed, including large-inventory selection/language retention and logical checkbox ordering.
- HA 2026.11.2 and 2026.8.2: 112 tests passed on each, including built-in room temperature versus target while Off without a comparison sensor.
- Local Chrome EN/HE screenshots reviewed with 100 fictional zones and 2,000 signals. Zone selection and language switching remained responsive; selected signals survived locale change. Standalone icons are decorative fallbacks, not proof of native HA graphics.
- Package/hygiene checks passed. Real HA icon rendering and reported CPU pause remain pending installed validation. No production installation, restart, study start or device control performed. HA remains 0.16.1; package is 0.16.3.

## Authorized deployment verified
Installed corrected 0.16.3 archive after on-host integration/storage backups. All 51 files verified against the archive and three saved storage files stayed byte-identical during each installation pass. Deployment exposed a stale frontend marker; corrected const.py, added build-time manifest/static/version equality enforcement and mismatch/lifecycle regressions. An additional confirmed native HA restart and full browser reload loaded the correct 0.16.3 URL.

Live verification: all 61 setup icons and all 58 icons in the tested expanded climate view contained SVG graphics. Zone selection completed in approximately 0.3 seconds including automation round-trip; Hebrew switching was immediate and retained the selection. These are spot checks, not a universal performance benchmark. EN/HE checkbox/icon/name alignment and built-in thermostat default were visually verified. No new 0.16.3 icon console errors appeared. No study started, device control activated or notification preferences changed. Private proof screenshots remain outside the repository.

Final validation: 77 core tests, 54 JavaScript tests, and 112 HA tests on each supported version passed. Corrected ZIP SHA-256: ccc663826c3512070d51187375d8fc356acbec888f97544ff5ebc7a206a258f5.
