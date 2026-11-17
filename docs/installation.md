# Installable preview 0.1.0

This experimental custom integration adds an **admin-only** ShabbatFlow sidebar panel. It previews schedules and optionally reads calendar entities. It cannot control devices, activate automations or run schedules. The bundled rooms and dates are fictional. It is not yet a family-access or production scheduling release.

## Install

1. Obtain `shabbat-flow-0.1.0.zip` and its SHA-256 file from a successful GitHub Actions **checks** run (artifact `shabbat-flow-preview`), or build locally with `python3 scripts/build_ha.py --check --zip`.
2. Back up any existing `custom_components/shabbat_flow` folder before replacing it. Unzip into the HA configuration directory: the resulting path must be `custom_components/shabbat_flow/manifest.json`, without another nested directory.
3. Restart Home Assistant yourself, then open **Settings → Devices & services → Add integration → ShabbatFlow Preview**. Confirm setup.
4. As an administrator, open **ShabbatFlow Preview** in the sidebar. Switch English/עברית, review the fictional example, and generate a preview. No device commands will be sent.

No HACS installation is required or currently provided. HA package tests use **Home Assistant 2026.11.2 / Python 3.14**; other versions, a full HA boot, live household deployment and browser/Companion interaction have not yet been verified. Test this preview before relying on its presentation.

## Calendar source

The default is the built-in [Jewish Calendar integration](https://www.home-assistant.io/integrations/jewish_calendar/) (`jewish_calendar`). Configure that integration's location, timezone, Israel/diaspora and candle-lighting/Havdalah settings in HA. ShabbatFlow does not change them or calculate its own zmanim.

Discovery uses entity-registry provider/translation keys, not display names. It looks for upcoming candle lighting, upcoming Havdalah, sunrise and `issur_melacha_in_effect`. Missing, disabled, ambiguous, unavailable and invalid values remain unresolved. Under the ShabbatFlow integration's **Options**, select explicit entities if discovery cannot resolve them, or choose **Manual date/time entry**. Manual mode remains available without Jewish Calendar; the manifest uses optional startup ordering rather than a mandatory provider dependency.

In **Advanced setup → Calendar**, review dates and click **Use installed calendar value** where appropriate. Importing is explicit and never overwrites the full plan automatically. Inputs use date/time controls in the plan's displayed IANA timezone, preserving seconds. Nonexistent DST times are rejected; repeated times require an offset choice. Timestamp sensors must supply explicit UTC offsets; ordinary naive `input_datetime` states are rejected.

**Current sensor values are not a future multi-day calendar.** Today's sunrise may not be the upcoming Shabbat's sunrise. Upcoming candle lighting and Havdalah do not necessarily describe every day of a continuous holiday. Supply and review all dated segments, room windows and meals before previewing. A full date-range provider adapter is a later iteration. The active-observance sensor is information only and does not lock or execute the plan.

## Storage, upgrade and removal

The integration stores only its own options/config entry through HA. Drafts are saved explicitly in this browser's local storage; browsers/users sharing an origin can share that storage. It is not encrypted family storage or a multi-user plan database. Clear a draft using the app's delete action, and keep exports/private mappings out of the public repository.

To upgrade, retain a copy of the previous integration folder, replace this folder with the new package and restart HA. To roll back, restore that folder and restart. Back up browser exports separately if needed.

To remove, delete the ShabbatFlow integration entry under Devices & services. This removes its panel and disables its API; static assets/routes remain registered until restart. Remove the integration folder and restart to finish removal. Existing devices and automations are unaffected.

## התקנה ושימוש בעברית

זוהי תצוגה מקדימה ניסיונית למנהלי המערכת בלבד; אין הפעלת מכשירים או אוטומציות. חלצו את הקובץ לתיקיית ההגדרות של HA כך שהקובץ `manifest.json` יהיה בתוך `custom_components/shabbat_flow`. הפעילו מחדש את HA והוסיפו את **ShabbatFlow Preview** דרך הגדרות ← מכשירים ושירותים ← הוספת אינטגרציה. פתחו את הלוח ובחרו עברית.

ברירת המחדל היא **Jewish Calendar** המובנית. באפשרויות ניתן לבחור חיישנים במפורש או להזין תאריך ושעה ידנית. בדקו את הגדרות המיקום, ישראל/חו״ל וזמני ההדלקה וההבדלה באינטגרציית המקור. זמני החיישנים הנוכחיים אינם לוח מלא לכל ימי החג: יש לבדוק את התאריכים ואת כל מקטעי התוכנית. הדוגמה בדיונית. טיוטות נשמרות בדפדפן רק לפי בקשה. להסרה, מחקו את רשומת האינטגרציה, הסירו את התיקייה והפעילו מחדש את HA.
