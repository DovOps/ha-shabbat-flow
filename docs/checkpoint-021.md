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
