# Rehearse your actual weekend plan

Available in package 0.21.0; installation and household hardware acceptance are separate from implementation.

1. Open your saved weekend draft and preview it. Resolve any incomplete choices.
2. Choose **Rehearse this exact plan**, then **Load scenarios from this preview**. Dates and calendar anchors remain unchanged.
3. Choose a compiled moment, such as candle lighting, night changeover, bathroom daylight break, morning or nap. Names are hints; the listed actions are the source of truth.
4. Choose **Run this transition only** to test only actions at that instant. Choose **Set up this moment** to apply the last known planned state of each selected device. Unknown prior states are left untouched.
5. Select areas, then **Simulate / review changes**. Shared bathrooms must be selected separately. Nothing changes during simulation.
6. For a supervised weekday test, select eligible lighting devices, record previous On/Off verification and review any ownership exclusions. Explicitly confirm **Apply test now**. The review expires after two minutes; reload if needed.
7. Refresh results, walk around, and add feedback. Download the JSON to retain the exact plan and before/after evidence.
8. Use **Review restore** if desired. Only confirmed changes still carrying this test's state/context can be restored. Outside changes and uncertain outcomes are skipped. Review and explicitly apply the selected restoration.

Start with one area and one transition. Test candle setup, night changeover, morning and bathroom daylight breaks separately. A test never arms, advances or edits the upcoming weekend schedule. Changing the draft requires a fresh review.

## Current limits

Real tests support the current qualified binary-lighting pilot only. HVAC, fans and appliances are visible for simulation but cannot be actuated here. A known inactive Jewish Calendar issur signal is required for physical tests. Existing automation writers remain blocked; they are never disabled. Rehearsal cannot overlap an armed control run on the same targets.

Stop prevents remaining commands; an already-issued command may finish. Restart interrupts the batch without replay or automatic restore. Results are point observations, not a continuous climate study. Up to 20 tests are retained for 90 days; export anything you want to keep. This panel does not certify device qualification automatically or select which rooms will be controlled during the actual weekend.
