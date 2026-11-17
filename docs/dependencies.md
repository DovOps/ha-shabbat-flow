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
