# Checkpoint 001: specification bootstrap and local preview

## Ready to review
- Official source-based Spec Kit templates/scripts, constitution, functional and nonfunctional requirements, plan, contracts, tasks and test traceability.
- Product roadmap with household feedback/history analysis; separate upcoming specification for extensible schedule groups, sleeping/recreation usage and sleep timing profiles.
- Local multilingual preview with English/Hebrew defaults, RTL, room dependencies, meals, independent HVAC/lighting offsets, bedroom sleep-light cutoff, draft save/load/delete and JSON export.
- Original cyan candle-and-flow logo. No third-party Home Assistant logo derivative in repository assets.
- Dependency decision document: selected-entity/provider-neutral approach is proposed; actual live providers and third-party integrations need owner review before adoption.

## Run and review
Follow README.md. Review `specs/001-preview-planner/verification.md` for 30 passing automated checks and browser evidence/limits. The final visual recheck is pending; earlier screenshots are explicitly labeled as earlier UI versions. Only fictional configuration is present.

## Next decisions
Checkpoint commit/push authorized on 2026-11-17. Choose a project license before public release. Next implementation should generalize the sample into configurable schedule groups and room-use profiles (feature 002), then inventory live provider contracts read-only. No live plugin dependency, calendar source, executor or production deployment is approved by this checkpoint.

## Follow-up requirements and branding
The local header now uses the approved original turquoise logo. Multi-day Shabbat/Yom Tov planning is specified in [feature 003](../specs/003-multiday-observance/spec.md), including the preferred “issur melacha in effect” live status input and separate future dated calendar coverage. This remains planned work, not current preview functionality. This checkpoint includes repository publication only; no HA changes are authorized or made.
