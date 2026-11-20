# Feature 009 — Guided room setup and bathroom dependencies

**Status:** Preview 0.8.0 installed and verified, including area label bindings and combined common-area profiles.
**Created:** 2026-11-17
**Branch:** `002-planning-foundation`
**Input:** Select rooms first, configure one room at a time, explicitly link bathrooms and simplify lighting/HVAC choices. Include functional and nonfunctional requirements.

This feature builds on 007 (live HA household inventory) and 008 (automatic Jewish Calendar dates). It changes permanent household setup, not weekly occupancy decisions. The installed sample remains preview-only. Verification and remaining limitations are recorded in `verification.md`.

## User stories and acceptance scenarios

### US1 — Configure a manageable set of rooms (P1)
As a homeowner, I select HA areas and configure one at a time instead of editing every area in a long form.

1. Given live inventory, selecting three rooms shows only those rooms in the setup queue, with their HA floor/name and progress such as “Room 1 of 3.”
2. A room can support sleeping and recreation independently. Early/standard/late sleep timing is chosen in the dated plan; setup explains its defaults.
3. Save & next persists the current room. Reloading or reopening setup resumes at an unfinished room and retains completed choices.
4. Skip for now leaves the room visibly unfinished. It produces no direct or indirect schedule actions. A summary distinguishes selected, ready and unfinished rooms and permits editing each one.
5. A shared/service area can supply bathroom lighting without requiring a fictitious sleeping or recreation use.

### US2 — Link a bathroom once (P1)
As a homeowner, I select the bathroom used by a room and review the relevant switches, without assigning the same lights repeatedly.

1. A room can link zero, one or more explicitly chosen HA areas. The application does not infer bathroom relationships from names.
2. After choosing a bathroom, its area-scoped light/switch candidates appear. Show all areas remains available for incorrectly assigned devices. Lights are selected once for that bathroom.
3. Linking another room to that bathroom reuses its existing configuration and clearly lists the linked rooms.
4. Each link chooses room-use-window lighting or whole-observance lighting when that linked room is selected for use in the dated plan. Whole-observance means the complete supplied continuous Shabbat/Yom Tov period, not just its first day.
5. Two overlapping or touching demands for the same bathroom lights produce a continuous on interval and one final off. Disjoint demands remain separate. Removing one link does not remove another room's demand.
6. A bathroom may instead or additionally be needed whenever anyone is home. This follows explicit dated home intervals; away intervals alone create no demand, and unset availability prevents a complete preview. No bedroom link is required.
7. A linked bathroom awaiting setup is visibly unresolved. The dependent room cannot be marked ready until the bathroom is ready or the link is removed. No partial dependent schedule is generated silently.

### US3 — Choose practical lighting and HVAC defaults (P1)
As a homeowner, I see the devices relevant to the current room and can copy a supported current HVAC setting without typing a raw profile.

1. Lighting choices distinguish main lights from night/background lights. The setup explains that sleeping main lights turn off at the chosen bedtime and recreation lighting follows room use.
2. HVAC offers three distinct scheduling choices: On/Off only preserving settings, a specified heating/cooling profile (including copy-current as a shortcut), and Do not schedule this HVAC. Copying current settings is a reviewed snapshot, never a live binding or a device command.
3. HVAC controls use supported modes, temperature units/ranges and available fan options. Off, unavailable, missing, unsupported or conflicting settings require explicit adjustment or leaving HVAC unscheduled; the application never guesses a mode.
4. Multiple HVAC devices with incompatible settings are not silently given one shared profile. The UI explains the conflict and allows choosing a compatible subset or leaving them unscheduled.
5. HVAC lead time remains independent of lighting changeover, anchored to the room-use schedule. Labels cover both heating and cooling.

### US4 — Review before weekly planning (P1)
The final summary lists ready rooms, their purposes, lights, HVAC intent, bathroom links and unfinished items. Opening the dated planner uses only ready configuration and automatically sourced upcoming dates. Weekly room use, sleep timing, meals and home/away choices stay in the planner. Editing setup never mutates an existing workspace snapshot.

## Functional requirements

| ID | Requirement |
| --- | --- |
| WIZ-FR-001 | Provide a room-selection step using current HA areas/floors, followed by one selected room at a time, with labelled progress, Back, Save & next and Skip for now. Allow adding/removing rooms and editing from the summary. |
| WIZ-FR-002 | Support independent sleeping/recreation purposes and shared/service configuration. Preserve the distinction between a room's supported uses and its dated planned use. Do not request individual identities. |
| WIZ-FR-003 | Persist selection, configuration and completion state in ShabbatFlow's HA Store. Resume unfinished setup across browser sessions. Keep in-progress edits on validation/network/storage failure; acknowledge completion only after successful persistence. |
| WIZ-FR-004 | Keep unfinished/skipped rooms out of configuration compilation, including their HVAC and bathroom demands. Display exclusions. Require at least one valid schedulable configuration for a new workspace. |
| WIZ-FR-005 | Show area-scoped light/switch and HVAC candidates first, retaining explicit all-area search/selection and missing-reference warnings. Never auto-select new devices or infer occupancy from activity. |
| WIZ-FR-006 | Configure bathroom lighting once per HA area and reuse its stable physical loads across explicit room links. Expose linked rooms and explain that editing the bathroom affects all links. No transitive/cyclic dependency expansion. |
| WIZ-FR-007 | Support per-link use-window or whole-observance demand and a bathroom-level whenever-anyone-is-home option. Union concurrent identical demands, retain provenance and avoid premature off events across rooms and multi-day boundaries. |
| WIZ-FR-008 | Validate bathroom readiness and removed/excluded references before a dependent room becomes ready. Explain the corrective step; never silently drop a required bathroom. |
| WIZ-FR-009 | Offer leave-existing-control, copy-current-HVAC and explicit adjustment using supported capabilities. Read only allowlisted current mode/target/fan values; show their observation time. Copy only on user action and preserve copied settings during inventory refresh. |
| WIZ-FR-010 | Keep HVAC preconditioning independent of lighting and support both heat and cool. Enforce capability compatibility across selected devices; unavailable/unsupported values require correction or opt-out. |
| WIZ-FR-011 | Provide a compact summary with Edit actions, counts and readiness warnings. Save per room, then open the existing dated planner using feature 008 automatic calendar data and its advanced manual override. |
| WIZ-FR-012 | Preserve existing saved household mappings through a versioned, tested migration. Existing valid configurations retain their semantics; do not reinterpret legacy shared-area use windows as whole-observance demand. Invalid references remain visible for review. |
| WIZ-FR-013 | Preserve the settings-revision and structural-inventory checks from 007. Inventory updates cannot erase unsaved wizard edits; another browser's save produces a recoverable conflict rather than lost updates. |

### US5 — Scan planned On and Off actions (P1, follow-up)
The final schedule preview must make On and Off actions immediately distinguishable rather than render all actions as green badges.

1. Given a preview containing both binary On and Off events, each event has its own action badge. On and Off use distinct semantic color treatments consistently across devices and days; they never share the same green treatment.
2. Every badge also has explicit localized action text (English/Hebrew). The action remains understandable without color, in RTL, and at mobile size. Badge text must have at least 4.5:1 contrast against its background.
3. HVAC Off uses the Off treatment. Heating and cooling retain explicit mode labels and cannot be mistaken for Off. An informational/tracked action or warning must not acquire an On badge merely because the row renders successfully.
4. Styling follows the planned action, not the device's current HA state or the validity of the plan. Badges do not imply that an action has executed.
5. Verification uses mixed On/Off and HVAC events in the same preview, checks distinct semantic classes and readable labels, and visually checks both languages at desktop and mobile widths. Schedule events, timings and digest remain unchanged by styling.

| Follow-up ID | Functional requirement |
| --- | --- |
| WIZ-FR-014 | The final schedule preview shall render separate, visibly distinct color-coded badges for planned On and Off actions on each event, with consistent semantic colors and explicit localized text. Cover binary switches/lights and HVAC Off versus active heating/cooling, preserve non-color readability and contrast, and do not conflate action state with validation or execution status. Acceptance: US5. |

## Nonfunctional requirements

| ID | Requirement and verification target |
| --- | --- |
| WIZ-NFR-001 | Multilingual UI with English and Hebrew supported by default. Every new label, help message, error and progress state has catalog parity; verify RTL, including mixed-direction HA names/entity IDs. Language changes preserve selections and schedule semantics. |
| WIZ-NFR-002 | All steps are keyboard-operable with associated labels, visible focus and semantic controls. After navigation, focus moves to the new step heading; errors are announced in a live region and focusable. Verify at 360px mobile width and desktop with no page-level horizontal scrolling. |
| WIZ-NFR-003 | No device-control calls, automation changes, HA registry writes or recorder changes. Writes are confined to this integration's settings. No external runtime/UI dependency is introduced. |
| WIZ-NFR-004 | Maintain admin authentication, request bounds and existing 20-area/100-load limits, counting included bathroom/service areas. Preserve repository separation: only fictional fixtures; no real family names, mappings, credentials or household screenshots in tracked files. |
| WIZ-NFR-005 | Settings writes are atomic and revision-checked. Test failed writes, disconnected requests, double submission, stale inventory, competing browser saves and reload/resume. Failed saves must not mark a room complete or advance the wizard. |
| WIZ-NFR-006 | Compilation is deterministic for identical normalized setup, calendar and dated plan. Test overlapping, touching and disjoint bathroom intervals, two/three-day observances, unset/away availability and incomplete rooms. Shared loads retain one physical identity. |
| WIZ-NFR-007 | Live HVAC telemetry changes do not change the structural inventory revision or overwrite a chosen profile. Area, capability, enabled-state and identity changes still require review. Current-state reads must not expose arbitrary attributes or histories. |
| WIZ-NFR-008 | Render only the active room's detailed controls. Keep visible inventory refresh within the existing 30-second bound; skip polling when hidden. Measure usability at the supported 20-area/100-load limit without adding per-entity request loops. |
| WIZ-NFR-009 | Regression tests cover old settings migration, stored progress, calendar/manual-override behavior and untouched existing workspace snapshots. Run Python, Node, repository hygiene and package checks, plus HA compatibility tests on 2026.8.2 and 2026.11.2. |
| WIZ-NFR-010 | Deploy a fully versioned static tree with a recoverable integration/settings backup. Verify English/Hebrew wizard and automatic dates in the installed app. Do not save fabricated mappings or overwrite another tab's unsaved household edits during verification. |

## Design decisions and limits

- Choose rooms → configure each room → review summary → plan dates/usage. Retain advanced controls behind clearly labelled disclosure, not as the first screen.
- Linking an unconfigured bathroom adds a visibly pending shared-area setup step; it does not implicitly approve its devices. Multiple links reuse that step.
- The legacy `none` choice is labelled “Do not schedule this HVAC.” It remains unscheduled on upgrade; it is never silently reinterpreted as power-only scheduling.
- The home-wide bathroom option requires compiler support for explicit home intervals; storing a flag without integrating it into preview is insufficient.
- Recent-use ranking is a subsequent enhancement, not a prerequisite for this wizard. It requires a bounded history contract, coverage/confidence labels and an unknown-history fallback. Area-scoped candidates and current HVAC snapshots are the initial simplifications.
- Recorder pattern analysis, automatic inferred mappings, automatic activation, family non-admin access and chat/MCP remain separate roadmap items. No new external dependency or third-party design is adopted.


## Setup feedback promoted to requirements
Bathroom-label filtering and additional role/area labels are now approved in US7 below.

## US6 — Schedule HVAC power without overriding settings (P1)
The homeowner selects an HVAC device and schedules On/Off while leaving its heating/cooling mode, target temperature and fan setting to the device/integration.

| ID | Requirement |
| --- | --- |
| WIZ-FR-015 | Offer “Schedule On/Off only — preserve settings,” “Use a specific profile,” and “Do not schedule this HVAC” as distinct intents in setup and summary. Power-only uses the independent HVAC lead time and room-use end to generate typed HVAC On/Off events, without mode, temperature, unit or fan overrides. It works with a currently-off device and does not require target/fan metadata. Require at least one selected HVAC device and a Sleeping/Recreation purpose to provide a dated use window; shared/service-only areas must receive actionable guidance instead of a silent no-op. |
| WIZ-FR-016 | Show power-only HVAC events in the final preview, with distinct On/Off badges and a “preserve settings” explanation. Read HA's advertised turn-on/off support as diagnostic information only. Unsupported/unknown support and unverified resume semantics are visible. Never fall back to a guessed mode or treat advertised TURN_ON as proof of restoration. Future execution must verify a device-specific power/resume adapter before activation; this release emits intentions only. |
| WIZ-NFR-011 | Test power-only versus specific-profile versus unscheduled behavior, HVAC-only rooms, currently-off devices, absent temperature/fan metadata, overlapping demands, incompatible intents, strict rejection of setting overrides in power actions, unchanged legacy settings, and multilingual summaries. No actuator or HA control service calls are introduced. |

Acceptance: a used room with power-only HVAC produces an On event at use start minus its lead time (clamped to the supplied preparation start) and an Off at use end, regardless of its current heat/cool/off state; the actions contain no explicit settings. Unscheduled HVAC produces neither event. Explicit profiles retain their existing target/mode behavior. Old saved `none` choices and existing workspace snapshots remain unchanged; a user explicitly selects power-only, saves, and opens a new workspace to use it. Devices reporting no native power support still allow an explicitly labelled intention preview, never a claim of executable compatibility.

## US7 — Optional HA labels simplify setup (P1, approved follow-up)
Before choosing rooms, homeowners may map existing HA labels to Bathroom lights, Room main lights, Background/night lights, Bedroom areas and Common areas. Suggested names are examples, never reserved names or automatically adopted mappings.

| ID | Requirement |
| --- | --- |
| WIZ-FR-017 | Read the HA label registry and area/device/entity label IDs. Persist optional label mappings (the original five, extended by WIZ-FR-035) by stable ID in ShabbatFlow settings. Offer an explicit no-label fallback and editing from every wizard stage. Never create or modify HA labels. |
| WIZ-FR-018 | Filter main/night lighting candidates by the chosen role label and current area. A match on the entity or its parent device qualifies; area labels never implicitly label all its lights. Bathroom/service main lighting uses the bathroom label when configured. Keep selected entities visible even when they no longer match. Provide separate Show all devices for this room and Show devices from all areas controls; HVAC remains domain/area-scoped. |
| WIZ-FR-019 | Filter bathroom area choices to areas containing light/switch entities matching the configured bathroom label (entity or device). Keep existing links visible, allow Show all bathroom areas, and explicitly review lights once per bathroom. Unassigned labeled lights remain accessible through all-area selection; labels never infer which bedroom shares which bathroom. |
| WIZ-FR-020 | Offer Bedroom/Common Area filters for selecting HA areas, retaining selected areas and a Show all rooms fallback. Area labels suggest sleeping/recreation purposes only through an explicit Apply suggestions action; support both labels and preserve existing purposes. Never auto-select rooms or entities, mark rooms ready, or alter a dated workspace from a label change. |
| WIZ-FR-021 | Provide a Tips documentation page and localized in-app guidance explaining area assignment, entity versus device labeling, example role labels, room-use labels, missing-label recovery and explicit review. |
| WIZ-NFR-012 | Include label identities/names/membership in structural inventory revisions. Preserve unsaved label mappings and room edits during polling and reject stale saves. Deleted mapped labels remain visible with a warning and all-device fallback; renames retain ID mappings. Unknown saved IDs may be retained, but newly submitted nonexistent label IDs are rejected. Legacy clients omitting mappings preserve saved mappings. |
| WIZ-NFR-013 | Test label-free migration, entity/device matching, area-only labels, deleted/renamed labels, overlapping label roles, selected exceptions, disabled/unassigned entities, stale writes, persistence and unchanged compilation. Use registry snapshots without per-entity requests. Verify EN/HE and mobile layout. |

Acceptance: creating or changing labels in HA refreshes candidate filters without changing selections; choosing labels and saving survives reload; clearing mappings restores area-only choices. No new external dependency, device execution or HA registry mutation is introduced.

## US8 — Bathroom daylight and night-light policies
Bathroom demand (explicit links/home availability) is separate from how its main and night lights run. No sunlight or occupancy is inferred from device activity.

| ID | Requirement |
| --- | --- |
| WIZ-FR-022 | Offer Always on and Daylight break per shared/bathroom area. New setups default Always on; new bathroom links default whole-observance demand. Preserve existing saved link timing and legacy lighting behavior unless explicitly changed. Always on means throughout the applicable demand, not when the house/linked rooms are unused. |
| WIZ-FR-023 | Daylight break defaults to sunrise +180 minutes through sunset −120 minutes, configurable from 0–360 minutes each. Apply each local day of a 1–3-day observance, clipped to demand and period boundaries. Turn both main and night lighting off during the break and restore the appropriate lighting afterwards. |
| WIZ-FR-024 | Optionally switch main lights to separately selected night/background lights at candle lighting +360 minutes (configurable 0–720), returning main lights at sunrise +0 minutes (configurable 0–180). Require both light sets to enable this policy. Daylight break and night switchover are independent. Invalid night windows keep both sets on; no guessed substitute timing. |
| WIZ-FR-025 | Read optional dated sunset from Jewish Calendar daily Shkia events. Preserve snapshots without sunset. Missing, ambiguous or invalid sunset disables the affected day's daylight break, retaining lighting and showing a localized preview warning. Invalid daylight intervals also retain lighting with a warning. Candle lighting remains the evening anchor; sunset is only the daylight-return anchor. |
| WIZ-NFR-014 | Union bathroom lighting demands after policy clipping so one room cannot prematurely switch off another room's bathroom. Test shared/home overlap, disjoint windows, empty windows, old configurations, 1/2/3-day periods, DST-aware timestamps, missing sunset, offsets and night-light switchover. Preserve deterministic preview, EN/HE, no actuators and snapshot immutability. |

Defaults are suggestions requiring explicit configuration, not religious guidance. A bathroom without adequate daylight should retain Always on. Night switching applies only when explicitly enabled. Existing main/night device selections alone do not enable it.

## US9 — Complete evening, morning and meal changeovers
| ID | Requirement |
| --- | --- |
| WIZ-FR-026 | Provide reusable background, kitchen and hallway night presets plus explicit custom/no-phase choices. Background lights start when a recreation use ends and default to off at sunrise −60 minutes. Kitchen night mode defaults to candle lighting +360 minutes, island/night lights until sunrise +120 minutes, then main lights while home. Hallway mode defaults to night lights from candle lighting until sunrise −60 minutes. No room names or device names are hard-coded. |
| WIZ-FR-027 | Expose independent night-start candle offset, night-end sunrise offset, morning-main sunrise offset and evening-main enablement. Home-driven phases follow explicit availability; recreation-end phases follow explicit used-room choices. Invalid/empty phase intervals emit no reversed events and show a preview warning. New workspaces default recreation rooms with mapped background lights to recreation-end background switching; existing exported snapshots remain unchanged. |
| WIZ-FR-028 | Allow each room to opt into evening and/or daytime meal lighting/HVAC. Populate meal target groups in new plans; only Family/Hosting meals activate them. Evening meals also trigger the room's recreation-end background lighting at meal end when enabled; lunch does not trigger night lighting. Use main lighting and selected HVAC intent with its independent preconditioning lead. Away/No meal do not activate these groups. Show linked rooms in the simple meal UI. Overlapping home, recreation and meal demands union without premature off. |
| WIZ-FR-029 | Provide a global Post-observance shutoff option, default false for new workspaces. With false, omit release/off commands at the final observance boundary while retaining internal night/morning/daylight transitions. With true, emit normal boundary releases. This is an end-policy choice, not an instruction to disable existing HA automations. |
| WIZ-NFR-015 | Test main-to-night-to-morning timelines, separate HVAC timing, meal Family/Hosting versus Away/No meal, shared demand union, empty intervals, multi-day/DST behavior and final-boundary policy. No household data from user exports enters fixtures or repository docs. No live device execution or external-automation ownership is implied. |

## US10 — Explain room completion and save blockers
| ID | Requirement |
| --- | --- |
| WIZ-FR-030 | Replace ambiguous unfinished status with distinct Ready, Draft awaiting completion, and Needs attention states. Show actionable validation reasons beside the room heading, in review cards and near Save & next. A valid draft explains that Save & next completes it; Save progress retains its draft status. |
| WIZ-FR-031 | Inventory changes, conflicting saved revisions, connectivity failures and server save errors must remain visible near save controls. Offer a Refresh inventory action for inventory review, preserving draft selections. Failed saves must not erase the explanation when the form redraws. Never silently discard edits or automatically acknowledge a conflicting saved revision. |
| WIZ-NFR-016 | Problems use a red, high-contrast treatment plus warning icon and text, never color alone. Announce changes accessibly and focus the explanation after blocked completion. Support English/Hebrew and RTL; test draft preservation, stale inventory recovery, validation and failed-save messaging. |

## US11 — Common areas distinct from bathrooms
| ID | Requirement |
| --- | --- |
| WIZ-FR-032 | Explicitly distinguish Bedroom, Bathroom, Common Area and Hallway, independently from Sleeping/Recreation purposes. Common areas can use meal lighting/HVAC, home-driven night/morning lighting and optional daylight breaks without a sleeping/recreation purpose or bathroom link. Bathroom links remain optional for non-bathroom rooms; explicit bathrooms cannot link recursively. |
| WIZ-FR-033 | Compose daylight breaks with night/morning and meal profiles. During the configured sunrise/sunset break, suppress all selected main/night lighting demand, including meal lights, while preserving HVAC demand and sleeping shutoff commands. Outside the break restore only lighting still required. Missing/invalid sunset retains lighting with a visible warning. Apply per day, preserving union, DST and final-shutoff behavior. |
| WIZ-FR-034 | Preserve legacy service-area semantics until explicit classification. Do not infer bathroom type from names; label suggestions follow WIZ-FR-035 and never reclassify existing rooms silently. On explicit Common area conversion, keep devices/meals/daylight settings; convert an existing bathroom night policy into home-driven phases only if no general phases exist, otherwise retain the configured general phases, and disable the competing legacy night policy. Explain this conversion. Common-area main lights use the main-light label, not the bathroom label. |
| WIZ-NFR-017 | Test common-only meal/HVAC saves, classification persistence and legacy preservation, conversion without device loss, combined daylight/night/meal timelines across 1–3 days, missing sunset, HVAC independence, and English/Hebrew UI. Upgrade preserves production settings and never commands devices. |

Hallway classification exposes the explicit hallway night preset (candles to sunrise −60 minutes, adjustable); no devices, meals or HVAC are selected automatically. Room type follows homeowner use, not the HA display name. Sleeping and recreation remain independent purposes.

| ID | Requirement |
| --- | --- |
| WIZ-FR-035 | Bind Bedroom/Common Area/Bathroom area/Hallway area labels separately from entity light-role labels. Suggest types using direct HA area labels only; unique matches default newly selected empty areas. Existing configured areas require Apply suggested area type; explicit types remain fixed across refreshes. Conflicting matches require explicit choice. Common Area labels do not imply recreation or sleeping. Preserve the original five-label request format and saved mappings when adding the two new area bindings. |

## US12 — Bedroom naps and independent late wake-up (preview 0.10.0)
A homeowner can plan daytime rest in selected bedrooms and keep overnight HVAC running later in rooms where people sleep in. These choices describe room use, not identities or ages; an office configured for sleeping is eligible too. Existing Early/Standard/Late bedtime profiles must not be presented as an independent wake-up control.

| ID | Requirement |
| --- | --- |
| WIZ-FR-036 | In each dated day panel, offer optional Nap time for rooms configured for sleeping, including a room not used overnight. Allow one or more explicit rest windows per room/day with enablement, start/end, independent HVAC preconditioning lead, and the room's reviewed HVAC intent. Nap defaults are reusable setup suggestions; actual dated nap selections belong to the weekly plan. New and migrated plans default to no naps. |
| WIZ-FR-037 | Offer an independent Wake-up / overnight HVAC-off choice per used bedroom/day: its existing default, Sleep late, or a custom time. Show the resulting local timestamp and allow an installer-defined sunrise offset or explicit dated local time. Changing wake-up must not move bedtime, bedroom lights-off, other rooms' settings or an unrelated recreation/meal schedule. Define Sleep late through a visible configurable time, never an assumed age or universal hour. |
| WIZ-FR-038 | Nap HVAC begins at nap start minus the chosen lead, clipped to supplied preparation/period coverage, and releases at nap end unless another compatible demand still requires that unit. Power-only nap and extended-sleep profiles preserve existing mode/temperature/fan; a specific profile is used only when explicitly selected. Do not schedule this HVAC remains respected and must explain why no HVAC events are produced. |
| WIZ-FR-039 | Nap mode is HVAC-only by default: it must not reuse overnight lighting-off rules, enable bedroom lighting, change main/night lighting phases or automatically create new bathroom demand. Offer an explicit option to include a linked bathroom during the nap; when selected it follows that bathroom's existing daylight/night policy. Existing independent bathroom demand remains intact. |
| WIZ-FR-040 | Union compatible overnight, late-wake, nap, recreation and meal demands for each physical HVAC unit. A late wake-up overlapping a nap must not introduce an intermediate Off/On pair. Incompatible HVAC settings or overlapping existing-control intent require visible conflict resolution, never silent last-writer-wins behavior. Nap/wake windows outside calendar coverage or inconsistent with explicit away periods block completion with an actionable explanation. |
| WIZ-FR-041 | Show overnight and nap windows, preconditioning and wake-up release times in the day summary, event reasons, whole-period HVAC chart and PDF. Preserve actual dated selections across save/load/export and explicit copy-day review for 1–3-day observances. A wake-up change applies only to the selected room/day unless the user explicitly updates reusable defaults. |
| WIZ-NFR-018 | Test no-nap backward compatibility, nap-only use without an overnight stay, independent bedtime/wake timing, power-only and explicit profiles, lead-time clipping, overlap union and conflicts, shared bathrooms, away/coverage errors, multi-day copy and DST gaps/folds. The same normalized inputs must give the same events and digest. Existing saved setups and exported snapshots remain unchanged until explicitly edited. |
| WIZ-NFR-019 | Provide English/Hebrew controls and explanations using the multilingual catalogs, RTL and accessible date/time controls. Keep common choices simple; expose additional windows/offsets progressively without raw timestamp or JSON entry. No identity/occupancy inference, new runtime dependency, device command or automatic activation is introduced by this requirement. |

Acceptance examples (fictional):
1. Bedroom A has an overnight HVAC end of 08:00. Select wake-up at 10:30: HVAC release moves to 10:30 while the previous evening's bedtime and lights-off stay unchanged.
2. Bedroom B is unused overnight but selected for a 14:00–16:00 nap with 30-minute preconditioning. Its HVAC demand is 13:30–16:00; no bedroom-lighting or bathroom commands are added by default.
3. An overnight demand ends at 14:30 and a compatible nap demand begins at 13:30. The shared HVAC stays continuously demanded until the later release; it does not cycle off at 14:30.
4. A two-day holiday can have a late wake-up on day one and a nap on day two. Copying a day's choices requires review of the target day's dated times and calendar anchors.
5. A nap conflicts with an away interval, an ambiguous clock time, or another demand with a different temperature: the planner explains the specific conflict and does not silently approve it.

## US13 — Meal HVAC and circulation Day / Night / Off
- WIZ-FR-042: Separate evening/daytime meal lighting and HVAC bindings per area, preserving legacy combined bindings unless explicitly edited. Allow daytime HVAC without sleeping/recreation purposes, and independently opt recreation HVAC out. Keep preserve-settings intent and independent preconditioning. Show linked lighting and HVAC groups under each meal; room presence and historical continuous operation never automatically enable HVAC.
- WIZ-FR-043: Offer selected main lights Always on while home, independent of bathroom daylight masks and meal/room use. Applicable examples are entrance access and bathroom convenience circuits. Follow explicit per-day home availability and existing final-release policy. Never select extra circuits automatically. Reject conflicting main-light phase choices rather than silently overriding them.
- WIZ-FR-044: Offer night/background lighting starting at candle offset or end of entertaining. End of entertaining is the latest end of that segment's planned evening recreation or home evening meal (starts before sunrise); absent either, use candles +360 minutes with a visible explanation. This is a planned event, not observed occupancy. Optional main lights switch off at that transition; bounded morning main-light windows use sunrise offsets and end in Off. Existing per-room after-use background lighting remains available.
- WIZ-FR-045: Allow night-light release ownership to be Planner or Existing automation. Existing means the planner emits On only and warns that the morning cutoff is external, unverified and not represented in the chart; it neither creates an Off nor changes existing automations. A known recorded timer is not silently imported. Planner-owned morning release remains configurable. Make Day/Night/Off and always-on exceptions understandable in setup and preview.
- WIZ-NFR-020: Additive settings; old saved setups/workspaces preserve their schedules. EN/HE and accessible controls. Validate incompatible always-on/daylight/phase choices, role requirements and bounded morning intervals. Test meal independence, power-only intent, away clipping, end-of-entertaining changes, multi-day/DST behavior, external ownership, final no-shutoff and no inferred initial Off. No new runtime dependency or execution path. Do not import household identifiers or history into reusable fixtures.

## Product identity and navigation follow-up (0.15.1)
- UI-FR-001: Show Shabbat Flow as the integration, config-entry default, sidebar and panel title; keep preview/observe-only limitations separate from its name. Retain domain, panel path, storage IDs and approved logo. Migrate only the exact legacy default config-entry title; preserve homeowner-customized titles.
- UI-FR-002: House setup, climate studies and settings use a shared responsive navigation-bar presentation with EN/HE labels, current-page indication and keyboard focus. The installed plan view includes the same destinations with Plan preview marked current. Navigation does not save, enable or execute anything implicitly.
- UI-FR-003: Settings dependency tiles use pale lime-green for detected/available, amber for needs-setup, and neutral gray for missing optional capabilities. Retain explicit status text and icons; status colors reflect actual discovery results, not user enablement or proven delivery.
- UI-NFR-001: Maintain readable contrast, 44px navigation targets, mobile wrapping and RTL. Test display-name migration/default-title preservation and package parity. No device-control, notification enablement or provider-setting behavior changes. Installation/restart is separately authorized and reported, not implied by packaging.

## Explainable choices, HA icons and flexible rest timing
- UI-FR-004: Show selected-option explanations directly below area type, preset, night phase, release ownership, daylight, HVAC intent and bathroom-link controls. Explain that choosing a preset replaces related phase values immediately but not device/HVAC selections, and requires saving. Describe every preset in the EN/HE user guide. Explain applicability to bedrooms and interaction with sleep profiles; no hidden policy changes.
- UI-FR-005: Use HA-assigned area and entity icons in room setup, planner room tiles, schedule events and climate-study selection. Prefer entity registry customization over state/original icon; use HA frontend icon rendering and decorative fallbacks if unavailable. Native select options may remain text-only. Names and accessible labels remain visible. Icon metadata must not affect compilation or device ownership.
- WIZ-FR-046: Bedroom reusable nap-start and late-wake defaults offer sunrise offset or local clock time. Nap end offers duration, local clock time or the selected observance-day boundary. Existing defaults retain sunrise/duration semantics. Dated plans resolve choices into explicit timezone-aware timestamps, allow review/edit, and reject ambiguous/nonexistent local times rather than silently choosing a DST fold.
- WIZ-FR-047: Present minute-based rest and lighting-phase offsets/durations as HH:MM, including signed sunrise offsets, with anchor/direction text. Preserve integer minutes in storage/compiler contracts. Clock times are distinct time-of-day controls; durations must not wrap at 24 hours. Invalid text cannot silently become zero or alter saved data.
- UI-NFR-002: EN/HE helper parity, RTL, keyboard access, aria-describedby for selected guidance. No hover-only help. Missing/invalid/custom icons never block planning and never introduce remote asset requests. Icon refresh is presentation-only. Verify unchanged legacy rest defaults, clock-time resolution, until-end nap, invalid duration and DST boundaries. No device controls or HA installation implied.

Acceptance: select each night mode and see a distinct explanation; apply and review every preset; preserve old nap defaults; set a 14:00 nap ending at the day boundary and an 11:00 wake time; verify in both languages. HA icon overrides appear without changing the compiled plan. Standalone renders labeled fallbacks.

## Icon and alignment correction
- UI-FR-006: Keep entity/area icons beside their names in setup choices and summaries, planner tiles, event rows, lighting/HVAC timeline labels and climate-study choices. Native dropdown option text remains the documented exception. Group each icon and label as one start-aligned unit; checkboxes remain on the opposite edge in EN/HE.
- UI-NFR-003: Render HA custom icons in the HA document where their nested components are registered; reuse copied SVGs by icon name in the planner iframe. Bound missing-icon waits and retain labeled fallbacks. Do not add an icon dependency or make device calls.
