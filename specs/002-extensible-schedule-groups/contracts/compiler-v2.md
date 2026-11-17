# V2 preview contract (local prototype)

The compiler consumes `{config, plan}` and returns preview-only events or an incomplete-plan diagnostic. No executor exists. Initial supported actions are idempotent binary states and explicit HVAC heat/cool/off settings. Scene/script/cycle adapters remain unsupported rather than inheriting unsafe replay semantics.

## Configuration
`schema_version: 2`; `rooms`: IDs to EN/HE labels; `loads`: logical IDs to `{label, physical_id, owner, kind, capabilities}`. `kind` is `binary` or `hvac`. Binary capabilities are `{}`. HVAC capabilities specify `modes`, `unit`, `min_temperature`, `max_temperature`, and `fan_modes`. Aliases for a physical load must agree on owner/kind/capabilities. Values describe fictional configured capabilities until HA verification exists.

`groups`: IDs to `{label, track_only, rules}`. Each rule has `id`, `targets`, `start`, `end`, `action`, `release`. A point action has null end/release. A maintained interval has both an end and release action. Shared overlapping demands for the same action are unioned; contradictory demands fail. At a boundary, a continuing/new demand takes precedence over the release of an ending demand. Conflicting releases fail when no demand continues. Explicit point commands conflicting with an active interval fail. Track-only entries produce observations on the preview, never state-setting intents.

`profiles`: IDs to `{label, room, purpose, groups}`. Profiles may also define an optional `window` with `start`/`end` default expressions using candle-lighting/sunrise offsets or explicit dated times. These are UI defaults for new choices; existing plan windows remain authoritative. Early/standard/late/custom are installer-defined profiles with independent rule timings, not hardcoded ages. Per-room profiles map to explicit groups; groups may be reused for shared dependencies. Configuration limits: 100 rooms/loads/groups/profiles, 50 rules per group, 100 targets per rule. Expanded preview limit: 10,000 demands/points, checked while expanding.

Actions: binary `{type: "state", state: "on"|"off"}`; HVAC off `{type:"hvac", mode:"off"}`; heat/cool `{type:"hvac", mode, temperature, unit, fan_mode}`. Validate every rule and release against every target, even inactive groups. Finite numeric temperatures only. No inferred HVAC mode.

Times: `{anchor: "candle_lighting"|"sunrise"|"use_start"|"use_end", offset_minutes: integer}` (bounded ±1440); or `{at: explicit offset-aware timestamp}` for a dated fixed rule. Calendar anchor references resolve within each selected segment. Use anchors resolve to the selected use/meal/manual window. All resolved instants must fit period preparation/end coverage. Never silently clip.

## Plan
`schema_version: 2`, `language`, `snapshot` (foundation calendar contract), `availability`, `room_uses`, `meals`, `groups`.
- Availability: contiguous `{id,start,end,state}` windows from preparation through final end; state home/away/unset. Unknown windows keep the draft incomplete.
- Room uses: foundation fields plus `segment`; profile must belong to selected room/purpose. Existing-control uses have no profile and generate no actions. Any same-room overlap remains an explicit unresolved conflict in this increment.
- Meals: `{id,segment,kind,choice,start,end,groups}`. Kind is a configurable stable slot ID. Choice unset/none/away/family/hosting. Explicitly provide at least one meal declaration per segment; `none` permits fast/no-meal profiles, extra slots are allowed. Home meals need home coverage across their setup-through-cleanup window. Groups activate only for family/hosting.
- Manual groups: `{id,segment,group,start,end}`. Explicit selections independent of room/meal eligibility; use for homeowner-selected catch-alls or optional outdoor profiles.

Uses and meal windows may cross segment boundaries but must overlap their named segment; full period bounds still apply. Multiple uses/meals and all three days are compiled together; no automatic reset at segment boundaries. Incomplete choices return zero events with localized diagnostic codes. No calendar status sensor gates event generation yet.

## Output
`preview_only`, `complete`, `issues`, `digest`, `events`. Completeness means draft selections and compiler validation only, not deployment approval. Events carry stable ID, local/UTC time, physical target, action, intent (`set_state` or `track_only`) and all originating selection/segment/group/rule reasons. Action events deduplicate aliases and identical state requests; no initial device state is assumed. Output remains advisory.

Digest excludes display language/labels and normalizes unordered catalogs/selection lists. Calendar segment order remains significant. No network, I/O or mutation in compiler. Existing v1 API and browser storage are unchanged; v2 is a separate opt-in preview endpoint until migration is ready.
