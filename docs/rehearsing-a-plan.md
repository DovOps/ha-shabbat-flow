# Rehearse your actual weekend plan

Available in package 0.22.0; installation and household hardware acceptance are separate from implementation.

1. Open your saved weekend draft and preview it. Resolve any incomplete choices.
2. Choose **Rehearse this exact plan**, then **Load scenarios from this preview**. Dates and calendar anchors remain unchanged.
3. Choose a compiled moment, such as candle lighting, night changeover, bathroom daylight break, morning or nap. Names are hints; the listed actions are the source of truth.
4. Choose **Run this transition only** to test only actions at that instant. Choose **Set up this moment** to apply the last known planned state of each selected device. Unknown prior states are left untouched.
5. Select areas, then **Simulate / review changes**. Shared bathrooms must be selected separately. Nothing changes during simulation.
6. For a supervised weekday test, select eligible lighting, HVAC or room fan devices, record previous On/Off verification and review any ownership exclusions. Explicitly confirm **Apply test now**. The review expires after two minutes; reload if needed.
7. Refresh results, walk around, and add feedback. Download the JSON to retain the exact plan and before/after evidence.
8. Use **Review restore** if desired. Only confirmed changes still carrying this test's state/context can be restored. Outside changes and uncertain outcomes are skipped. Review and explicitly apply the selected restoration.

Start with one area and one transition. Test candle setup, night changeover, morning and bathroom daylight breaks separately. A test never arms, advances or edits the upcoming weekend schedule. Changing the draft requires a fresh review.

## Current limits

Immediate rehearsals support qualified lighting, HVAC power and independently mapped room fans. Scheduled weekend execution is still lighting-only. Appliances remain simulation-only. A known inactive Jewish Calendar issur signal is required for physical tests. Existing automation writers remain blocked; they are never disabled. Rehearsal cannot overlap an armed control run on the same targets.

Stop prevents remaining commands; an already-issued command may finish. Restart interrupts the batch without replay or automatic restore. Results are point observations, not a continuous climate study. Up to 20 tests are retained for 90 days; export anything you want to keep. This panel does not certify device qualification automatically or select which rooms will be controlled during the actual weekend.

## HVAC and fans
For an off HVAC unit whose previous mode is unknown, first turn it on yourself in HA with the mode/temperature you want. Choose **Capture current settings (no device changes)** in its rehearsal review. You can then turn it off yourself and review a planned On scenario. A confirmed Off rehearsal also remembers its starting mode/speed. Captures expire after 90 days and are tied to device identity.

HVAC tests are power-only even if your plan has temperature presets. Review shows active/captured mode and current target settings. No climate temperature, preset or fan-mode changes are sent. If the unit itself resets its target, preservation fails; there is no automatic correction.

Native fans preserve reviewed speed/preset; off fans need a capture while running. Switch-backed fans are power-only. Assign fans in room setup and give them explicit activity windows to produce events. Assignment alone does not create a schedule. Tests do not automatically qualify devices for scheduled control.

New duration-based naps that exceed a short planning day end at that day's boundary, with an adjacent explanation. Invalid explicit clock windows show an error beside Add nap. Permanent defaults and existing naps remain unchanged.

The shared adoption playbook is bundled as **Guide** in app navigation and linked next to rehearsal controls. The public version is available at https://dovops.io/ha-shabbat-flow/docs/adoption/ . Source: `src/shabbat_flow/web/adoption-guide.json`; update English and Hebrew together. Help opens separately to preserve unsaved plan edits.
