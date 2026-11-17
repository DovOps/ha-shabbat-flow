# Reuse assessment

Reviewed 2026-11-17. Sources inspected read-only; no code copied into runtime.

## Good Days
https://github.com/bareli/good_days at `4e5921231fd5e6d2d086ac711f81251921551c6a`.
Source evidence: `custom_components/good_days/timers.py` (`expand`, `conflicts`), `timer_manager.py` (`_async_run`, `async_execute`), README.

Already provides local calendar, Hebrew/English, profiles, candle/Havdalah-relative timers, fixed times, previews, same-minute conflicts, presets and one-shot execution. It deserves reuse evaluation; a second general timer engine is not justified yet.

Observed differences: conditions are checked at firing time against mutable rules/profile; `async_execute` delegates on/off via HA services. Our desired product compiles room/meal dependencies into a reviewed snapshot and eventually needs explicit climate targets and independent room-specific heating/cooling comfort, planned/observed feedback and identity-free setup. Frozen-plan semantics, arbitrary shared dependencies and controlled automation ownership were not established by the inspected paths. This is not an exhaustive audit or a tested compatibility claim.

Decision: build the reusable household plan/preview layer independently. Defer executor choice. A later adapter spike must test Good Days API stability, input export, dated/frozen semantics, climate settings, DST/multi-day recovery and license/dependency compatibility. Prefer contributing or integrating when it meets the contract; do not fork prematurely. No dependency or version guarantee is asserted now.

## Calendar and HA UI
https://www.home-assistant.io/integrations/jewish_calendar/ provides local configured calendar information; production must validate actual location/conventions, not accept library defaults blindly.
https://contributors.home-assistant.io/frontend/custom-ui/card/ documents the native custom card route. The first local web preview is a development harness, not a replacement claim for native HA authentication/UI.

## Clarifications
Confirmed: candle lighting for evening offsets; sunrise rules separate; HVAC/lighting independent; multilingual including RTL; existing boiler automations preserved; no PII in project; no commit/push before checkpoint review. Deferred: real mapping/defaults, calendar source, freeze/late edits, production executor, license choice, HA compatibility, other observance types.
