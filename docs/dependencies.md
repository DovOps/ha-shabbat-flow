# Dependency decisions — review before integration

## Current accepted set
Python 3.11+ standard library and a modern browser. Node 18+ is a development test tool only. Official Spec Kit templates/scripts are development scaffolding, with provenance and license recorded. No HA runtime, custom integration, remote calendar service, frontend card library or copied third-party runtime/UI design is required by the preview. The original logo is a generated project asset.

## Explicit approval gate
Inspection of Good Days and other Shabbat dashboards was research only. Do not copy their source, UI design, branding or introduce mandatory/optional package dependencies without first presenting scope and alternatives to the owner. No association, endorsement or compatibility is claimed. A research candidate is not an adopted dependency.

## Proposed provider-neutral production contract (not implemented)
Setup lets the owner map existing HA entities to semantic inputs. Required planning data: dated candle-lighting, sunrise and agreed observance-end timestamps, timezone, observance category and coverage for the requested period. The preferred active-observance input is the homeowner-mapped “issur melacha in effect” binary sensor, covering Shabbat and Yom Tov. It is the live status signal, not a substitute for a dated future calendar. A current binary state alone cannot supply future schedule anchors.

Verify timestamp units/timezones, intended date, source settings, freshness, unavailable/unknown states, next-event rollover, multi-day semantics and future date coverage. Store provenance and dated snapshots. Never derive candle lighting using an unconfirmed sunset offset. An entity label does not establish its provider. Actual home entity IDs stay outside public examples.

Selected entities may come from different installed integrations without source-level coupling if they satisfy this contract. Missing required data blocks plan approval with a localized explanation. A validated frozen plan may remain usable through later sensor rollover/outage only under an explicit execution policy; that policy is deferred.

## HA dependency terminology
Integration `dependencies` in manifest.json concern HA integration setup; `after_dependencies` expresses optional ordering when applicable. Python `requirements` are separate library dependencies. Selecting an entity is not importing its custom integration. Declaring a custom integration dependency is not a promise to install/configure it for the user.

Reference: https://contributors.home-assistant.io/core/integrations/manifest/

Before R2, present actual providers, required fields, supported versions, install/configuration steps, missing-data behavior and alternatives. Obtain the owner's decision before incorporating provider-specific APIs, third-party UI designs, libraries or an executor. Read-only inspection does not change the production installation.

Multi-day planning is specified in `specs/003-multiday-observance/spec.md`: obtain the entire continuous period and its per-day anchors before approval. A status sensor remaining on across a day boundary must not prevent the next day’s preplanned meal/profile events. No provider package is selected by this requirement.

## Future optional MCP/chat adapter
Feature 005 is an approved future requirement, not an approved package selection. Evaluate the installed HA version’s MCP/LLM API extension support, scoped permissions and network/authentication requirements before deciding between HA-native exposure and a separate thin adapter. The current loopback harness remains local and unauthenticated; it is not a remote MCP server.

## Installable sample and default calendar direction
Feature 006 uses HA built-ins `frontend`, `http` and `panel_custom` only; no third-party runtime package is added. The user-selected default is HA's built-in Jewish Calendar (`jewish_calendar`), with optional startup ordering and registry-based discovery verified against HA 2026.11.2 source. Compatibility is tested with HA 2026.8.2 and 2026.11.2. Manual mode remains available without the provider. Optional selected-entity reads are an initial bridge, not a claim of full provider compatibility or multi-day future coverage.

Development compatibility tests install Home Assistant 2026.11.2, pytest 9.2.0 and pytest-asyncio 1.5.0 in an isolated Python 3.14 environment. These are test dependencies, not bundled packages. The installable sample runs within HA and uses its supplied libraries.

Feature 007 uses HA's built-in area/floor/device/entity registry helpers and `helpers.storage.Store`. No new external runtime dependency. Inventory synchronization uses visible-page polling (15 seconds and focus) against current registry snapshots, not a background service or external data store. Installation upgrade is explicitly authorized by the user.

Feature 008 uses the supported read-only `calendar.get_events` service and entity registry to read the installed Jewish Calendar daily/yearly entities. Provider selection uses registry metadata; no device service is exposed. No runtime library is added. Compatibility tests install the provider's own declared `hdate[astral]` dependency (1.2.1 for HA 2026.8.2; 1.2.2 for 2026.11.2) to exercise actual event generation. Source location, timezone, Israel/diaspora and candle/Havdalah offsets remain owned by Jewish Calendar. No changes to those settings are made.

Feature 009 reuses the existing HA registry/state reads and Store. Current HVAC reads are limited to mode, target temperature and supported fan setting. The wizard and bathroom demand policies add no external package or third-party design dependency.

Feature 009 power-only follow-up reads HA's `ClimateEntityFeature.TURN_ON/TURN_OFF` state flags as diagnostics. Inspection of the installed test runtime's HA 2026.8.2 `components/climate/__init__.py` confirms that the base `async_turn_on` can choose a mode. Flags therefore do not establish resume semantics. Typed `hvac_power` preview actions contain only on/off state; any future executor must verify a provider-specific adapter. No executor or extra dependency is introduced.

Feature 009 label filtering reads HA's built-in label registry and direct area/device/entity memberships. No external dependency, registry writes or third-party design is introduced.

Preview 0.7.0 reuses the accepted Jewish Calendar daily event feed for optional Shkia/sunset timestamps. Actual provider event generation is tested on both supported HA versions. No astronomical calculator, new external library, actuator or third-party design is added.

PDF export uses browser-native printing and the existing logo and language catalogs. No PDF library, external service or new runtime dependency is introduced.

## Feature 010 execution direction (accepted; observe-only checkpoint)
The proposed executor runs inside the existing HA integration using built-in storage, UTC event helpers and allowlisted service adapters. No third-party package or source is proposed. Review `specs/010-controlled-execution/spec.md` and `plan.md` before introducing execution. Native HVAC resume must be qualified per provider and installed unit; the generic HA climate fallback is insufficient. Automation introspection completeness and durable recovery guarantees require a compatibility spike. Preparing this specification authorizes no device or automation changes.

Observe-only 0.12.0 uses the HA automation component raw_config source behind its admin websocket, guarded for unavailable access, and HA’s built-in sun helper for external sun-trigger forecasts. No new package or source design is incorporated. Observation persistence uses Python standard-library atomic file replacement because the checked HA Store implementation can consume write errors. Native resume qualification and live execution remain deferred.

Forecast 0.12.1 also uses HA’s existing read-only target helper for literal label/area/device membership. Tested on both supported versions; no service dispatch, registry writes or new package.

Hourly thermal evidence (0.13.0) uses the existing HA state machine and entity/device/area registries only. Current weather temperature comes from a selected installed weather entity; no new provider, weather API call or dependency is introduced.

Feature 011 standalone climate studies reuse HA registries/state reads and the existing atomic observer storage, SVG renderer and native printing. No calendar service, new runtime dependency, external delivery or actuator is introduced.

## Feature 012 — optional lifecycle notification channels
User authorized discovery-based SMS and Companion App push implementation. The installed Twilio SMS UI 1.0.3 contract uses `twilio_sms_ui.send_message` with configured `from_number`, `target`, `message`; no third-party source copied or package installed. A completed service call is submitted/unconfirmed because this provider may catch upstream errors. Optional HA-native `notify.mobile_app_*` push uses the already-installed Companion App, selected explicitly. Uses documented iOS `url` / Android `clickAction` relative report paths: https://companion.home-assistant.io/docs/notifications/notifications-basic/ . No Nabu Casa subscription requirement is introduced by ShabbatFlow; remote report access depends on the user's existing HA connection.

Notifications are a separately opted-in outbound side effect; observe/preview still make zero actuator or automation-mutation calls. Both channels default off. Missing optional providers disable that channel without blocking planning/studies. Dedicated Settings performs read-only capability discovery, distinguishes requirement scopes and never installs/configures dependencies automatically. Jewish Calendar remains preferred with manual fallback.
