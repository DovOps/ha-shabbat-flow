# Checkpoint verification — 2026-11-17

## Executed checks
- Python unittest: **25 passed**, including compiler and real loopback HTTP transport tests.
- Node built-in test runner: **5 passed**, covering catalog parity, markup keys, draft envelope errors, missing translation handling and localized timezone display.
- Repository hygiene gate: passed. Hand-reviewed authored files contain fictional room labels and sample dates; no real home inventory/history, family names, personal document IDs, workstation paths or credentials were copied. Generated logo and sample-only screenshots were reviewed separately.
- Official Spec Kit `check-prerequisites.sh --json`: recognized active feature and its research/model/contracts/quickstart. Templates/scripts are a source snapshot; the legacy CLI bootstrap failed and no newer global CLI was installed.
- Sample benchmark: 100 compiles on Python 3.14 / Apple Silicon, median **0.109 ms**, maximum **0.653 ms**, 25 events. This is a local measurement, not a cross-platform performance guarantee. CI targets Python 3.11 but has not run remotely (nothing pushed).

## Browser checks performed
Local in-app browser: initial preview rendered; language switching translated controls, timeline reasons and validation, and mirrored Hebrew RTL. Saved a Hebrew draft, changed inputs, rejected a contradictory nobody-home plan, loaded the draft, reloaded the page and loaded again. Deleted the synthetic saved draft and verified the localized missing-draft message. Keyboard ArrowLeft adjusted bedroom conditioning from +5h to +4.75h without changing shared HVAC or lighting event times. All input/select controls had label associations.

At a 375px viewport override (360px client width after scrollbar), English and Hebrew document scrollWidth equaled clientWidth: no horizontal page overflow. Viewport override was reset. Export download was read back and matched the compiler output exactly at that revision. No real-house data was used.

Screenshots: `docs/screenshots/preview-en.jpg`, `preview-he.jpg` capture the initial UI check. They **predate** the later sleep-light control, sleeping-room wording and HVAC terminology changes; they are not evidence of final rendered text.

## Remaining checks and limits
The follow-up browser reload was declined by the browser permission gate. Browser automation stopped and was not retried through another route. The later sleep-light behavior is covered by automated compiler tests; final visual recheck is pending user review. Storage quota/disabled-storage errors have implementation handling but were not fault-injected in the browser. A full accessibility audit and independent Hebrew language review are not claimed.

Feature 001 is a limited local preview, not a production HA integration or complete schedule. It accepts supplied illustrative calendar anchors, does not calculate zmanim, and cannot activate devices. Room selection currently means sleeping rooms. Early/Standard/Late and recreation profiles, extensible typed schedule groups, live provider mapping, actual HVAC modes/targets, executor/ownership/recovery, feedback forms and history analysis remain future features.

No third-party HA runtime/UI design was adopted. No production configuration changes. No commits or pushes. Review the dependency decision and license choice before future public/production work.

## Logo and multi-day requirements follow-up
The header now references the approved local turquoise logo with responsive dimensions and an accessible brand name; the server exposes only the exact `/logo.png` asset path. Existing 25 Python and 5 Node checks and repository hygiene passed again. The local server was restarted. No new browser rendering verification was attempted because the earlier browser permission denial remains in effect. Feature 003 documents multi-day requirements only; the existing compiler continues to reject multi-day input.
