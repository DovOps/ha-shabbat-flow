# Checkpoint 033 — clearer planner actions and status

The planner now keeps Preview and Save visible inside a collapsible action drawer, with test/observe/arming commands grouped separately from exports and secondary tools. On mobile the sticky drawer starts collapsed and remembers an explicit choice for the tab. It collapses after navigation to a test or control section. No underlying activation operation or default changed.

A read-only Plans and studies overview distinguishes saved control, plan observations and climate studies. It shows persisted status, date range, selected/excluded control counts, blocked-device count, next pending action and review/report links. Approval is labeled NOT armed. The editable workspace is labeled separately; calculating differences against a frozen run is a later stage.

The compact authenticated status path skips inventory discovery and never dispatches device services. Existing full observation listings retain discovery for configuration pages.

Verification: 94 core tests, 72 web tests and 19 execution tests on each supported HA version pass; repository hygiene, bundle consistency and whitespace checks pass. Fictional English/Hebrew desktop/mobile layouts and keyboard drawer operation were checked. Collapsed mobile height was about 61 CSS pixels at a 360-pixel viewport. Real phone acceptance remains pending.

Deployment deliberately pending. No restart, device actuation, arming or household observation edits. Feature 022 contains the FR/NFR, implementation order and outstanding tasks for evidence reuse, ownership review, scheduled HVAC/fan support and recovery validation.


Stage 1 deployed as 0.22.3 after owner authorization: 77 installed files verified, four stores unchanged during installation, on-host backup and one HA restart. Installed planner shows the same scheduled observation and no active/pending control. No household settings, observation or activation changed. Later stages remain pending.
