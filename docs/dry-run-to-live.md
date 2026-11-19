# From a prediction-only weekend to live scheduling

Status: review plan, not an implemented executor. Version 0.11.0 previews intentions only. Installing it does not activate a schedule. This guide applies the roadmap's R3 execution gates and feature 004 feedback requirements without adding a dependency or authorizing device control.

## 1. Freeze the prediction before the weekend

Finish the room mappings, then open a **new** dated workspace so it captures those mappings. Verify provider dates/zmanim, home/away intervals, meals and hosting, bedroom sleep/wake and naps, independent HVAC preparation, and optional afternoon activity. Check each actual load, including access circuits, bathroom lights, main-to-background transitions and morning releases. Declare which existing automation owns each externally controlled cutoff; the current preview does not forecast those events.

Export both JSON and PDF before the earliest planned preparation action. Retain the exact files privately with the release version and export time. This is an operational baseline, not the future application's approval/freeze feature. Do not overwrite it after seeing history; create a separate revised copy. Capture starting device states and read-only history coverage where available. Verify relevant lights/HVAC have detailed history; do not change Recorder settings without separate authorization.

Ask about recurring needs before the assisted-operation period ends: which switches serve access, which short episodes are cleaning/task work, which lights deliberately remain on, HVAC preparation and wake-up preferences, and known exceptions. Record functions and reasons, not identities, in reusable material.

## 2. Observe normal operation

Keep existing automations and ordinary household routines unchanged. Do not ask anyone to follow the prediction: that would make agreement less informative. No interaction during observance is required. Review recollections after observance. Preserve any voluntarily recorded approximate timing as reported evidence, not a precise sensor timestamp.

The observation window should include the preparation lead-in, the full candle-to-final-end period and a short post-period tail. Collect history promptly after the weekend, within actual retention, including unknown/unavailable intervals and context where available. No background capture job is installed by this guide.

## 3. Compare prediction, observation and desired behavior

Use the frozen JSON and read-only history to report each physical load's planned windows, observed windows, differences in start/end and active duration, coverage and missing observations. Include relevant observed loads absent from the plan, not just the intersection. Score lighting separately from HVAC and separate always-on baseline loads from transition-heavy loads. A device already in the intended state does not require a matching transition.

Declare matching tolerances before scoring; suggested initial review bands are ±15 minutes for lighting transitions and ±30 minutes for HVAC preparation, subject to family confirmation. Report exact deviations too. Do not interpret these bands as actuator accuracy targets. Measure planned-versus-observed agreement only where both states are known; report the unknown and unscheduled fractions separately.

Classify differences as: missing binding, timing difference, intentional changed use, brief staff/task activity, existing-automation interaction, accidental left-on, device/history failure, or unresolved. Context evidence can identify some automation actions; an absent user ID is not proof of physical/manual action. User-reported operator attribution remains reported evidence.

History is not the ideal schedule. Ask whether a difference mattered: Was access available? Were bathrooms usable? Were bedrooms comfortable on entry and after waking? Did evening, lunch and nap HVAC meet needs? Was anything on needlessly? Rate lighting and HVAC separately 1–5, with not-applicable allowed; identify one-off versus recurring changes. Do not infer occupancy or who slept where from device states.

Deliver a private comparison report, a list of unresolved loads, and a proposed next-plan diff with rationale. Keep the original baseline intact. One weekend provides one trial, not seasonal validation.

## 4. Build the minimum execution path

Before implementing R3, review a specification and adapter decision covering:

- A server-persisted immutable approved plan, explicit arming before its first preparation event, expiry, ownership and an audit trail. Browser storage alone is insufficient.
- Per-load allowlists and one owner for each action. Inventory fixed-time, sun and known observance-state automations; resolve clashes explicitly. The existing-automation overlay is still deferred.
- Provider-specific HVAC resume semantics. Verify On/Off preserves the intended heat/cool mode and target; generic turn-on support alone is insufficient. Unsupported units stay excluded.
- Persistent event results, idempotency, bounded retries, unknown/unavailable handling, and a documented restart/power/network recovery policy. Never blindly replay stale events.
- A disarm/rollback procedure that stops future planner actions, describes what happens to current device states and restores only explicitly managed automation state. Disarm is not automatically an all-Off command.
- Local-time/DST, 1–3-day observance and end-policy tests; no default post-observance all-Off. No unreviewed cloud dependency or new messaging service.

A native HA executor is the preferred proposal for review, because planning already runs inside HA. This document does not select a third-party scheduler or introduce execution code.

## 5. Weekday pilot, then limited live use

Run an explicitly authorized weekday test on a small allowlist: one main/background pair, one access light and one representative HVAC unit at a time. Observe actual state and HVAC settings; test overlap, missed events, restart recovery, cancellation and rollback. A simulated virtual clock can test compiler cases but does not replace real-device verification. Recovery tests that restart HA require a suitable agreed window.

Then arm only validated devices for an initial live period. Keep unvalidated loads on explicitly agreed existing control; do not assume someone will be available to correct mistakes. Expand after reviewing actual results. Feature work, execution testing and authorization must all be complete before calling the system live.

Go/no-go: every included device mapped and ownership reviewed; essential access/bathroom needs covered; no unresolved schedule conflicts; verified HVAC semantics for included units; successful weekday actuation and recovery tests; reviewed final plan and fallback; explicit activation. One satisfactory history comparison alone is not a go-live gate.

## סדר העבודה בקצרה

גרסה 0.11.0 היא תצוגה מקדימה בלבד ואינה מפעילה מכשירים. לפני תחילת התוכנית יש להשלים מיפוי, לפתוח סביבת תכנון חדשה ולשמור JSON ו־PDF ללא שינוי בדיעבד. במהלך השבת ממשיכים בשגרה הקיימת. לאחריה משווים תכנון, היסטוריה ומשוב; משאירים חוסרים כלא־ידועים ומפרידים פעילות קצרה לצורכי עבודה מהתנהגות רצויה. לפני הפעלה חיה נדרשים תוכנית מאושרת ושמורה בשרת, בעלות ברורה על כל מכשיר, בדיקת שמירת הגדרות מיזוג, התאוששות מתקלות, אפשרות ביטול וניסוי מורשה ביום חול. מתחילים בקבוצה מצומצמת שנבדקה ומרחיבים לאחר ביקורת.
