# Installable preview 0.2.0

This experimental custom integration adds an **admin-only** ShabbatFlow sidebar panel. It previews schedules and optionally reads calendar entities. It cannot control devices, activate automations or run schedules. The installed entry point reads your HA areas and devices. The separate demo remains fictional. It is not yet a family-access or production scheduling release.

## Install

1. Obtain `shabbat-flow-0.2.0.zip` and its SHA-256 file from a successful GitHub Actions **checks** run (artifact `shabbat-flow-preview`), or build locally with `python3 scripts/build_ha.py --check --zip`.
2. Back up any existing `custom_components/shabbat_flow` folder before replacing it. Unzip into the HA configuration directory: the resulting path must be `custom_components/shabbat_flow/manifest.json`, without another nested directory.
3. Restart Home Assistant yourself, then open **Settings → Devices & services → Add integration → ShabbatFlow Preview**. Confirm setup.
4. As an administrator, open **ShabbatFlow Preview** in the sidebar. Switch English/עברית, include planning areas, select sleeping/recreation purposes, assign device roles and shared bathrooms, then save. Review the dated calendar inputs and open a household plan. No device commands will be sent.

No HACS installation is required or currently provided. HA package tests target **Home Assistant 2026.8.2 and 2026.11.2 / Python 3.14**. Companion-specific interaction remains unverified. Test this preview before relying on its presentation.

## Calendar source

The default is the built-in [Jewish Calendar integration](https://www.home-assistant.io/integrations/jewish_calendar/) (`jewish_calendar`). Configure that integration's location, timezone, Israel/diaspora and candle-lighting/Havdalah settings in HA. ShabbatFlow does not change them or calculate its own zmanim.

Discovery uses entity-registry provider/translation keys, not display names. It looks for upcoming candle lighting, upcoming Havdalah, sunrise and `issur_melacha_in_effect`. Missing, disabled, ambiguous, unavailable and invalid values remain unresolved. Under the ShabbatFlow integration's **Options**, select explicit entities if discovery cannot resolve them, or choose **Manual date/time entry**. Manual mode remains available without Jewish Calendar; the manifest uses optional startup ordering rather than a mandatory provider dependency.

In **Advanced setup → Calendar**, review dates and click **Use installed calendar value** where appropriate. Importing is explicit and never overwrites the full plan automatically. Inputs use date/time controls in the plan's displayed IANA timezone, preserving seconds. Nonexistent DST times are rejected; repeated times require an offset choice. Timestamp sensors must supply explicit UTC offsets; ordinary naive `input_datetime` states are rejected.

**Current sensor values are not a future multi-day calendar.** Today's sunrise may not be the upcoming Shabbat's sunrise. Upcoming candle lighting and Havdalah do not necessarily describe every day of a continuous holiday. Supply and review all dated segments, room windows and meals before previewing. A full date-range provider adapter is a later iteration. The active-observance sensor is information only and does not lock or execute the plan.

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

Room mappings persist in HA across restarts. Weekly workspace choices remain browser snapshots; later registry changes do not silently rewrite them. The initial date form creates one segment; review longer observances in Advanced setup. Jewish Calendar may not expose the future sunrise needed, so supply the correct dated value. Nothing executes.

Upgrade an existing entry by replacing the package and restarting; do not add a duplicate integration. Static asset paths include the release version to avoid mixed cached files. Back up the integration directory and ShabbatFlow storage before upgrades. Removal of the config entry does not erase household storage automatically.
