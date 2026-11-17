# Feature 009 — Guided room setup and bathroom dependencies

**Status:** Core wizard implemented in preview 0.4.0. Schedule badge follow-up (WIZ-FR-014) specified; implementation pending.
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
2. HVAC offers leave existing control, use current settings, and adjust settings. Copying current settings is a reviewed snapshot, never a live binding or a device command.
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
- “Leave existing control” generates no HVAC actions and does not suspend existing automations.
- The home-wide bathroom option requires compiler support for explicit home intervals; storing a flag without integrating it into preview is insufficient.
- Recent-use ranking is a subsequent enhancement, not a prerequisite for this wizard. It requires a bounded history contract, coverage/confidence labels and an unknown-history fallback. Area-scoped candidates and current HVAC snapshots are the initial simplifications.
- Recorder pattern analysis, automatic inferred mappings, automatic activation, family non-admin access and chat/MCP remain separate roadmap items. No new external dependency or third-party design is adopted.


## Setup feedback to consider separately
The homeowner may need to correct HA area associations for HVAC devices. An optional homeowner-selected HA label for bathroom-light candidates could make bathroom selection easier. This is a follow-up design candidate, not a mandatory label dependency or an implemented label filter: preserve explicit area/device selection as a fallback and never infer room-to-bathroom relationships merely from a light's label. No household registry or label changes are authorized by this specification update.
