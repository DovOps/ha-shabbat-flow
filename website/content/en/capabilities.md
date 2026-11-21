# What you can use today

| Capability | Current scope |
| --- | --- |
| Room wizard | HA area/device/entity discovery, label filters, room roles and shared bathrooms |
| Calendar | Jewish Calendar future event data; manual fallback; continuous multi-day periods |
| Plan previews | Lighting and separate HVAC profiles, meals, sleep, naps, night/morning phases |
| Visual reports | Event lists, lighting timelines, HVAC grids, JSON and native PDF / Print |
| Observation | Durable plan comparison and standalone 1–48-hour climate studies; collection gaps disclosed |
| Notifications | Optional discovered SMS/app channels and guarded pre-candle app reminders; explicit opt-in |
| Device execution | **Optional qualified lighting pilot; separate approval and scheduling. HVAC, fans and appliances excluded.** |
| Official HA verification | **Not confirmed. Independent custom integration.** |

## Dependencies, without surprises

The HA frontend, HTTP and custom-panel components host the integration. HA areas are needed for room setup; available climate entities are needed for climate studies. Jewish Calendar is preferred for automatic dates, with manual fallback. Weather, reference thermometers, labels, automation introspection, Twilio and Companion App push are optional. Settings shows detected/missing/needs-setup status and guidance.

Detection is not proof of phone delivery, complete holiday coverage or perfect automation prediction. Actual handset delivery and mobile PDF workflows require installation-specific validation.

## The path toward execution

The execution specification covers explicit activation, physical-load ownership, existing automation conflicts, provider-qualified HVAC power control that preserves settings, and restart recovery. The lighting subset is implemented with conservative ownership checks and bounded optional correction. Full HVAC/fan adapters, handoffs and live acceptance remain open. A saved plan never runs automatically: review, approval and explicit scheduling are required.

See the [maintained roadmap](reference/docs/roadmap.md) and [requirements status](reference/docs/requirements-status.md) for current implementation and validation boundaries.
