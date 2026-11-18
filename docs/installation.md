# Installable preview 0.8.0

This experimental custom integration adds an **admin-only** ShabbatFlow sidebar panel. It previews schedules and optionally reads calendar entities. It cannot control devices, activate automations or run schedules. The installed entry point reads your HA areas and devices. The separate demo remains fictional. It is not yet a family-access or production scheduling release.

## Install

1. Obtain `shabbat-flow-0.8.0.zip` and its SHA-256 file from a successful GitHub Actions **checks** run (artifact `shabbat-flow-preview`), or build locally with `python3 scripts/build_ha.py --check --zip`.
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
