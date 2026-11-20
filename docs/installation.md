# Installable preview 0.9.0

This experimental custom integration adds an **admin-only** ShabbatFlow sidebar panel. It previews schedules and optionally reads calendar entities. It cannot control devices, activate automations or run schedules. The installed entry point reads your HA areas and devices. The separate demo remains fictional. It is not yet a family-access or production scheduling release.

## Install

1. Obtain `shabbat-flow-0.9.0.zip` and its SHA-256 file from a successful GitHub Actions **checks** run (artifact `shabbat-flow-preview`), or build locally with `python3 scripts/build_ha.py --check --zip`.
2. Back up any existing `custom_components/shabbat_flow` folder before replacing it. Unzip into the HA configuration directory: the resulting path must be `custom_components/shabbat_flow/manifest.json`, without another nested directory.
3. Restart Home Assistant yourself, then open **Settings → Devices & services → Add integration → ShabbatFlow Preview**. Confirm setup.
4. As an administrator, open **ShabbatFlow Preview** in the sidebar. Switch English/עברית, include planning areas, select sleeping/recreation purposes, assign device roles and shared bathrooms, then save. Review the automatically sourced upcoming Shabbat/Yom Tov summary and open a household plan. No device commands will be sent.

No HACS installation is required or currently provided. HA package tests target **Home Assistant 2026.8.2 and 2026.11.2 / Python 3.14**. Companion-specific interaction remains unverified. Test this preview before relying on its presentation.

## Calendar source

The default is the built-in [Jewish Calendar integration](https://www.home-assistant.io/integrations/jewish_calendar/) (`jewish_calendar`). Configure that integration's location, timezone, Israel/diaspora and candle-lighting/Havdalah settings in HA. ShabbatFlow does not change them or calculate its own zmanim.

Discovery uses entity-registry provider/translation keys, not display names. It looks for upcoming candle lighting, upcoming Havdalah, sunrise and `issur_melacha_in_effect`. Missing, disabled, ambiguous, unavailable and invalid values remain unresolved. Under the ShabbatFlow integration's **Options**, select explicit entities if discovery cannot resolve them, or choose **Manual date/time entry**. Manual mode remains available without Jewish Calendar; the manifest uses optional startup ordering rather than a mandatory provider dependency.

House setup defaults to the **next not-yet-started Shabbat/Yom Tov**. Its daily/yearly calendar entities must be enabled, with sunrise, candle lighting and Havdalah events included. ShabbatFlow reads the provider's configured timezone and Israel/diaspora setting, and uses its location/offset calculations unchanged. No external calendar service or new runtime library is needed.

Review the local dates and each day's candle lighting, sunrise and planning-segment end. On consecutive holy days, the next candle-lighting anchor is the planning transition between daily segments; final Havdalah ends the whole period. These are planning divisions, not newly calculated halachic boundaries. The active-observance sensor remains informational.

**Advanced settings → Use manual dates instead** offers deliberate override. This starts one day, with further supplied segments available in the planner's Advanced setup. The regular date/time controls preserve offsets and reject invalid DST times. Automatic refresh never replaces manual entries. Existing planner workspaces retain their copied snapshots.

The adapter requires exactly one installed Jewish Calendar source and complete events within its bounded 14-day lookahead. It reports missing/disabled/unavailable/ambiguous sources instead of inventing times. An observance already underway is skipped. Manual mode remains available without the provider.

## Storage, upgrade and removal

The integration stores its options/config entry and reviewed household mappings in its own HA Store (`shabbat_flow.household`). No registry entries or existing automations are changed. Drafts are saved explicitly in this browser's local storage; browsers/users sharing an origin can share that storage. It is not encrypted family storage or a multi-user plan database. Clear a draft using the app's delete action, and keep exports/private mappings out of the public repository.

To upgrade, retain a copy of the previous integration folder, replace this folder with the new package and restart HA. To roll back, restore that folder and restart. Back up browser exports separately if needed.

To remove, delete the ShabbatFlow integration entry under Devices & services. This removes its panel and disables its API; static assets/routes remain registered until restart. Remove the integration folder and restart to finish removal. Existing devices and automations are unaffected.

## התקנה ושימוש בעברית

זוהי תצוגה מקדימה ניסיונית למנהלי המערכת בלבד; אין הפעלת מכשירים או אוטומציות. חלצו את הקובץ לתיקיית ההגדרות של HA כך שהקובץ `manifest.json` יהיה בתוך `custom_components/shabbat_flow`. הפעילו מחדש את HA והוסיפו את **ShabbatFlow Preview** דרך הגדרות ← מכשירים ושירותים ← הוספת אינטגרציה. פתחו את הלוח ובחרו עברית.

ברירת המחדל היא **Jewish Calendar** המובנית. באפשרויות ניתן לבחור חיישנים במפורש או להזין תאריך ושעה ידנית. בדקו את הגדרות המיקום, ישראל/חו״ל וזמני ההדלקה וההבדלה באינטגרציית המקור. זמני החיישנים הנוכחיים אינם לוח מלא לכל ימי החג: יש לבדוק את התאריכים ואת כל מקטעי התוכנית. המסך הראשי מציג אזורים ומכשירים מ־HA. בחרו מטרות שימוש, תפקידי תאורה ומיזוג וחדרי רחצה משותפים ושמרו. הדוגמה הנפרדת בדיונית. טיוטות נשמרות בדפדפן רק לפי בקשה. להסרה, מחקו את רשומת האינטגרציה, הסירו את התיקייה והפעילו מחדש את HA.

## Live household setup

Inventory refreshes every 15 seconds while visible, on focus and on manual refresh. Renames resolve through stable registry IDs. New devices are candidates only. Moves, missing/disabled devices and HVAC capability changes need review; unavailable mapped loads block workspace generation. Unsaved choices survive refresh, and stale saves are rejected. Choose **Reload saved choices** to discard local edits.

Include at most 20 areas and map at most 100 loads. Sleeping and recreation are independent purposes. Shared bathrooms must be included and mapped explicitly. When HVAC scheduling is enabled, mode, temperature and fan mode must match supported device capabilities; no settings are guessed. Devices without supported fan-mode metadata are not supported by this preview yet. Generated timing profiles are starting examples to review, not household recommendations.

Room mappings persist in HA across restarts. Weekly workspace choices remain browser snapshots; later registry changes do not silently rewrite them. Automatic mode reads the complete next observance, including one to three consecutive days, from the Jewish Calendar daily/yearly calendars. Missing calendar entities or events block automatic creation with guidance. Manual mode is under Advanced settings and starts a single supplied segment. Nothing executes.

Upgrade an existing entry by replacing the package and restarting; do not add a duplicate integration. Static asset paths include the release version to avoid mixed cached files. Back up the integration directory and ShabbatFlow storage before upgrades. Removal of the config entry does not erase household storage automatically.

גרסה 0.4.0 מציגה אוטומטית את השבת או החג הקרובים שטרם התחילו, עם זמני הדלקת נרות וזריחה לכל יום והבדלה סופית. יש להפעיל את היומנים היומי והשנתי של Jewish Calendar ואת האירועים המתאימים. הזנה ידנית זמינה בהגדרות מתקדמות בלבד ואינה נדרסת ברענון.


## Guided room setup (0.4.0)
Choose HA rooms, then configure one room at a time. Save & next marks a valid room ready; Save progress and Save unfinished & skip retain drafts. Reload resumes the first unfinished selected room. Ready rooms appear in the final summary; dated room use and meals are still chosen in the planner.

Link bathrooms explicitly. Configure their lights once, then reuse the same area from other rooms. A link can follow room-use windows or the full continuous observance when the linked room is used. Shared-area lights can also follow explicit home intervals. Editing a bathroom makes dependent rooms unfinished until reviewed again. Skipped rooms create no direct or shared demands. Identical overlapping/touching lighting demands merge; disjoint demands remain separate.

HVAC supports copying an available device's current heat/cool target and fan settings, or choosing supported settings manually. Multiple selected devices must agree for copying. Missing/unsupported fan metadata, off state or incompatible devices require adjustment or leaving existing control. No device is commanded. Recent-use ranking is deferred.

Existing schema-1 room mappings are migrated in memory with their original use-window semantics and persisted as schema 2 on the next successful settings save. The HA Store envelope stays version 1; the payload owns the household schema version. Back up both the integration and its own Store before upgrade. To roll back after saving new-format settings, restore both copies while HA is stopped.

בחרו חדרים, הגדירו כל חדר בנפרד ושמרו להמשך. ניתן לקשר חדר רחצה משותף ולהגדיר את התאורה פעם אחת. חדרים שטרם הושלמו אינם יוצרים פעולות בתכנון. הגדרות מיזוג נוכחיות מועתקות לבדיקה בלבד; אין הפעלת מכשירים.


## Power-only HVAC and action badges (0.5.1)
In a room's HVAC section, choose one of three scheduling intents:
- **Schedule On/Off only — preserve settings** creates typed HVAC power intentions, with no heating/cooling mode, temperature or fan commands. It accepts currently-off units and does not require target/fan metadata. The independent lead time is bounded by the supplied preparation start.
- **Use a specific heating/cooling profile** retains explicit validated settings and the copy-current shortcut.
- **Do not schedule this HVAC** emits no HVAC events. This is the clarified label for the previous “Leave existing HVAC control” choice; upgrades do not silently change existing choices.

Save the room and open a new dated planner, then select its use/profile. Existing workspace snapshots retain their earlier settings. Power-only preview events say “Preserve existing settings.” On badges are green; Off badges are dark slate with white text; active heating/cooling have separate mode colors. Tracked actions remain informational.

HA's advertised TURN_ON/TURN_OFF flags are shown as diagnostics only. The base climate turn-on fallback can select a mode, so these flags do not prove that an integration restores previous settings. This preview does not execute anything. A future executor must verify a device-specific resume adapter and refuse unsupported or unverified restoration; it must not substitute a guessed mode or setting-bearing command.

בתפריט המיזוג בחדר ניתן לבחור הפעלה וכיבוי בלבד תוך שמירת ההגדרות, פרופיל חימום/קירור מוגדר, או ללא תזמון. לאחר שמירה יש לפתוח מתכנן מתוארך חדש ולבחור שימוש בחדר. תגי הפעלה ירוקים ותגי כיבוי כהים, עם טקסט ברור. התאימות לשחזור ההגדרות במכשיר דורשת אימות לפני ביצוע עתידי.

Optional label mappings are available in house setup; see [Setup tips](setup-tips.md). No HA label changes are performed by the app.

## Night, morning and meal profiles (0.7.0)
Map main and night/background entities separately. In each room, expand **Night, morning and meal lighting** and choose a starting preset or adjust offsets. Kitchen mode uses the night role for island lights and the main role for spots; hallway mode uses the night role only. Recreation rooms with mapped background lights default to starting those lights when recreation use ends, through sunrise minus 60 minutes. Existing saved workspaces are not rewritten.

Select **Use main lighting / HVAC for lunch at home** for each room that should follow lunch; evening meals have a separate option. New dated plans list these linked rooms below each meal. Family/Hosting activates them; Away/No meal does not. HVAC intent and preconditioning remain separate from lighting. Home-driven morning main lights may remain on after a meal ends; identical demands union.

Shared/bathroom areas have their own **Bathroom lighting policy**. Always on retains lighting for the applicable demand. Daylight break defaults to sunrise +180 through sunset −120 minutes. Optional main/night switching defaults to candles +360 through sunrise. Choose both light sets before enabling it. Choose either bathroom-specific timing or general room phases to avoid contradictory policies.

New bathroom links default to whole-observance demand; existing links keep their timing until edited. Sunset is optional dated Jewish Calendar Shkia data. Missing or ambiguous sunset retains that day's lighting and produces a warning; manual calendars without sunset behave the same way. Night switch windows that cannot be resolved keep both bathroom sets on and warn.

**Switch scheduled devices off at the end of Shabbat / Yom Tov** defaults unchecked. New workspaces omit final-boundary release commands while retaining internal transitions. This does not switch off, suspend or take ownership of existing HA automations. The app still only previews schedules.

## Room completion feedback (0.7.1)
Red warning boxes explain validation and save blockers beside the room and its save controls. A draft with no validation problems explains that **Save & next** marks it ready, while **Save progress** leaves it excluded from dated room choices. Inventory review offers **Refresh inventory** without discarding edits. Conflicting saved revisions require deliberate review; **Reload saved setup** replaces unsaved edits. Server save failures remain visible after redraw.

## Area types and label suggestions (0.8.0)
Map existing HA area labels to Bedroom, Common Area, Bathroom and Hallway separately from light-role labels. Existing configured rooms require explicit type selection or Apply suggested area type, followed by Save & next. Common areas support meal lighting/HVAC, night/morning phases and optional daylight breaks together without a sleeping purpose or bathroom link. See [setup tips](setup-tips.md).

## PDF export (introduced in 0.8.1; included in installed 0.9.0)
The schedule page includes Export PDF / Print beside JSON. After a complete preview, use it and choose Save as PDF in the browser dialog. The report includes the logo, dated daily context, meals, room use, availability, warnings and schedule. Household plan details remain in the report; review before sharing. Edits require a fresh preview. Native HA app print support may vary; open in a browser when necessary. The user verified the local PDF export; the new chart layout still needs a final exported-PDF pagination check.

## Visual plan (0.9.0)
Generate a new workspace to capture area types and provider-supplied Hebrew date/parsha/holiday labels. The complete preview includes per-day lighting charts grouped by room type, plus the event list. Export PDF / Print includes the same charts and boxed day summaries. Unknown before the first scheduled state is hatched; On bars are planned intentions, never occupancy or confirmed device state. Existing automations may act differently. Time axes follow local calendar days and show UTC offsets at DST transitions. Missing provider metadata stays absent.

## HVAC chart (introduced in 0.9.1; live verification completed in 0.10.0)
The complete preview and PDF include a single first-candle-to-final-end HVAC chart for scheduled units. Small 30-minute cells distinguish planned On, Off and Unknown; cells containing transitions are split at exact times. Heating/cooling and preserve-settings control share the On/Off view; the detailed event list retains settings. Older workspaces can use this chart after re-previewing. The period follows actual anchors rather than assuming exactly 25 hours.

## Bedroom rest and afternoon hosting (0.10.0)
Refresh the integration page after upgrading. The dated planner adds independent bedroom HVAC wake-up overrides and optional HVAC-only nap windows, including preconditioning and explicitly selected shared bathroom lighting. Bedroom setup can store reusable rest defaults. Old plans without these fields retain their previous behavior. On Shabbat, use Add afternoon hosting / Seudah Shlishit, select Hosting and review lunch-linked rooms and times. Final-segment default is end minus 150 minutes; internal holiday boundaries require explicit review. These remain previews, not device automation execution.

## Circulation and independent meal HVAC (0.11.0)
Enable dinner/lunch HVAC independently from meal lighting in each common area's phase settings. Recreation HVAC can also be disabled independently. For access circuits use Always-on access lights. For hallway main/night circuits use Hallway Day / Night / Off and review morning start/end; its night transition follows the latest planned evening recreation or dinner end, falling back to candles +6h. A candle-time Hallway preset can explicitly turn main lights Off while night lights turn On.

Existing HA automation morning release emits only nightly On commands and warns that the external cutoff is not shown. It does not disable or duplicate that timer. Map each hallway/shelf/background circuit explicitly to its area and light role. These are preview capabilities; upgrading does not change household bindings. Save reviewed setup and open a new dated workspace after upgrading; old workspaces retain their prior choices.

Deployment verification: 0.11.0 was installed with an on-host backup, archive SHA-256 and byte-for-byte verification of all 33 packaged files. Saved household storage was unchanged. After restart, the live versioned panel loaded, saved ready mappings were present, and independent meal HVAC and circulation controls were inspected without saving edits. See [dry run and go-live plan](dry-run-to-live.md).

## Observe mode and unmanaged forecasts (0.12.1)

After a complete household preview, **Observe this plan — no device control** offers Start observing, saved runs, Stop, a summary table and Download plan + observation summary. Starting stores a server-compiled snapshot; it is separate from future approval/arming. You may close the browser. It samples once a minute and resumes after HA restart, marking the gap unknown. Initial and sampled device readings remain private in HA. Exports include household mappings and actual observed states; review before sharing. No device, automation or Recorder setting is changed.

Report-only recovery checks default to five minutes after boot and every 30 minutes; they can be disabled or configured (boot 1–60, repeat 5–1440 minutes) for the selected active run. They never correct device states in this release. Downloaded JSON includes the original plan, expected events, unmanaged forecast, per-event sampled outcomes, observed changes, power/settings comparison totals, gaps and collection status. Before the first planned state, comparison is unplanned; unavailable/restart gaps are unknown. One-minute sampling cannot identify every brief task-lighting episode. For exact retrospective transitions, compare Recorder history separately while retained.

Existing enabled automations with literal time or sun triggers, weekday-only conditions and supported On/Off actions (direct entities or literal label/area/device targets) appear as **Existing automation — unmanaged**, sorted with planner events and included in print/PDF. Their state is not added to planner charts or demand merging. Missing access, templates, scripts, state/issur conditions and template targets are explicitly unresolved, not silently ignored or forecast as certain. This is a bounded first overlay; full condition/action support and ownership handoffs remain future work.

Runs are stored in the integration's own `.storage/shabbat_flow.observe` integrity-checked file. Back it up with the integration before upgrades. Completed evidence expires after 90 days; limits are 20 runs, 100 mapped loads, 5,000 events and 96 hours per run. At 20,000 observed changes the export marks truncation; totals continue. A write/integrity error stops collection and is surfaced rather than resetting saved runs. Uninstall does not automatically erase the observation file. Earlier packages do not read it; restoring an older package stops observe collection.

מצב המעקב שומר תוכנית בשרת ודוגם מצבים פעם בדקה בלי להפעיל מכשירים. אפשר לסגור את הדפדפן. פערים באתחול נשארים לא ידועים. כפתור ההורדה כולל תוכנית וסיכום השוואה. בדיקות התאוששות ניתנות להגדרה אך מדווחות בלבד. אוטומציות זמן ושמש נתמכות מוצגות כלא־מנוהלות; תנאים או תסריטים שלא פוענחו מסומנים במפורש.

## Hourly thermal evidence (0.13.0)
Before starting a new observation, select the outdoor weather source. A single registered weather entity is selected automatically; with multiple sources, choose one explicitly or outdoor values will be missing. All enabled registered climate entities are observed, including rooms not scheduled for use, up to 100. Source and room identity are frozen for the run. No extra weather plugin, device service or sensor configuration is required.

The combined JSON export contains `run.thermal`: preparation-anchored hourly slots, thermostat current/target/range temperatures, mode (including heat/cool/off), enabled/off power, optional HVAC action, and contemporaneous current weather temperature. Raw values/units and normalized Celsius values are retained. Update age describes the HA state record, not a guaranteed physical measurement timestamp. An off thermostat may still report current and target temperatures; a missing attribute is null, never zero. Thermostat placement and weather-provider location limit comparisons: this evidence supports reviewing future setpoints, not automatic calibration.

A delayed slot over 90 seconds is missing, not backfilled with current temperature. Restart/clock rollback cannot duplicate an hourly slot. Existing active runs start thermal collection after upgrade and report when it was added; completed old runs are unchanged. Missing earlier hours remain unknown. Full data is included in Download plan + observation summary; the on-page summary reports collected/due snapshots and source. Thermal data does not enter preserve-settings matching or issue any control commands.

במעקב חדש ניתן לבחור מקור מזג אוויר. מקור יחיד נבחר אוטומטית; כשיש כמה מקורות יש לבחור אחד. דגימה שעתית כוללת תרמוסטטים רשומים ופעילים, טמפרטורה נוכחית ויעד, מצב חימום/קירור/כבוי ופעילות כאשר זמינה, יחד עם טמפרטורת החוץ. הנתונים המלאים בהורדה; שעות חסרות אינן מושלמות בדיעבד. אין שינוי הגדרות או כיול אוטומטי.

**Visual report:** choose a saved run and View observation summary for per-thermostat current/target/outdoor charts and hourly heat/cool/off markers. Expand Hourly readings for the table. Export observation PDF / Print produces a separate logo-branded report from that frozen run. Missing readings break lines; hourly dots do not imply continuous compressor activity. Charts appear as data arrives, not in an unobserved future plan.

**דוח חזותי:** בוחרים מעקב שמור ומציגים סיכום לקבלת תרשימי טמפרטורה ומצב שעתיים. ניתן לפתוח טבלת קריאות ולייצא דוח מעקב נפרד ל־PDF עם לוגו. נתונים חסרים מוצגים כפערים.

Reports group zones across the observation period: Active (observed On at least once), Inactive (no On observed, with some Off evidence), then Unknown. Active charts and combined hourly-table sections sort by observed On minutes from one-minute samples. Missing duration is separate; hourly dots are not used to estimate runtime. No-On evidence does not prove no brief use or an unoccupied room. Older exports without counters show duration unavailable.

Each associated zone chart includes planned room use (sleep/recreation/naps/meals where linked), planned lighting and separately observed lighting. Main/background circuits have separate rows. Missing associations/gaps remain explicit; no occupancy is inferred. The all-zone hourly table is also printed, with repeated column headers.

Deployment verification (2026-11-20): authorized 0.13.0 installation completed with an on-host backup of the previous integration and existing ShabbatFlow store. Archive SHA-256 and all 38 installed files verified; Python sources parsed and saved household bytes remained unchanged. After one HA restart, the live versioned 0.13.0 panel, saved setup, weather-source selector and observe/export controls loaded successfully. No saved observation runs were listed and no run was started. No device-control path was activated. Real hourly collection, real-data report review and native PDF pagination remain pending.

## Standalone Climate Study (0.14.0, packaged; not yet deployed)
Use **Climate Study — no Shabbat plan required** at the top of house setup. Select zones, 1–48 whole hours (default 24), associated lights/switches and optional room-temperature reference sensors. Same-area lighting is suggested but never automatically selected. Choose weather when multiple sources exist. Add an optional intended-use/comfort note, then **Start climate study now**. No calendar or completed room setup is needed. One standalone study can be active at a time; plan observation can coexist.

You may close the browser. Collection persists in HA, stops automatically or via Stop selected observation, and survives restarts with unknown gaps. Use Refresh saved runs, View observation summary, Export observation PDF / Print, or Download climate study + report data. Existing exports remain available after completion. Nothing controls devices. Reports show selected zones, observed lighting and optional thermostat-minus-reference differences, not plan compliance or certified calibration offsets. Without an independent reference there is no measurement-offset conclusion. Scheduling and summary delivery are not included.

Back up the integration and its observation Store before upgrading. Earlier releases cannot read standalone study records; a downgrade after starting a study requires exported evidence and restoring the matching pre-upgrade Store while HA is stopped. Current 0.14.0 reads existing plan observations unchanged.

מחקר אקלים עצמאי מאפשר לבחור אזורי מיזוג, תאורה וחיישני ייחוס למשך 1–48 שעות ללא תוכנית שבת. ההתחלה מיידית, הסיום אוטומטי וניתן לעצור מוקדם. אפשר לסגור את הדפדפן. הדוח וההורדה כוללים קריאות מדווחות ופערי איסוף; אין הפעלת מכשירים, הוכחת נוכחות או כיול אוטומטי. תזמון מחקרים ומשלוח סיכומים נדחו לשלב עתידי.

**Room activity signals (0.14.0):** select lights and any relevant room switches, including outlets or other non-lighting switches, as contextual signals alongside climate readings. Same-area membership includes an entity's device area when it has no explicit area. Nothing is selected automatically. Reports label switches separately from lights and preserve sampled On/Off changes. These may suggest activity but do not prove occupancy or manual operation; automated changes, devices left On and missed short episodes limit interpretation. The JSON fields `lights` and `study_lights` retain their names for compatibility and include both domains.

סימני פעילות בחדר יכולים לכלול תאורה וכל מתג רלוונטי, לרבות שקעים. יש לבחור אותם במפורש. בדוח מוצגים מתגים בנפרד מתאורה. שינויי הפעלה וכיבוי עשויים לרמוז על פעילות, אך אינם מוכיחים נוכחות או הפעלה ידנית.
