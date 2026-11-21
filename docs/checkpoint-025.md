# Checkpoint 025 — stored PDF downloads (0.19.1)

Lazy, server-rendered PDFs from saved report JSON or validated plan snapshots. Authenticated downloads, private disk cache, embedded English/Hebrew fonts, vector charts, feedback and per-zone thermal tables. No new observation or device control is activated. New ReportLab/Python bidi dependency choice approved by owner; the unavailable rlbidi extra is not used.

91 core, 64 JS and 123 HA tests per supported version passed. EN/HE brochure builds and 164-page / 7,588-link checks passed. See Feature 016 verification for cache, authorization and visual evidence. Deployment evidence follows install; real phone Open/Share acceptance remains a user check.

Deployment: 66 files installed with a component/storage backup; all three saved-store hashes unchanged. One HA restart loaded 0.19.0 and the approved PyPI requirements. The installed archive generated and downloaded actual English and Hebrew PDFs from a retained completed observation. The English file contains 25 pages in 787,261 bytes; a text-boundary check found no horizontal margin overflow. Ready dialogs expose Download, Open and Share / Save to Files. No study activation, device calls or feedback edits were performed. Mobile Companion App acceptance remains a user check.

Final 0.19.1 patch isolates PDF-cache startup I/O errors: planning/observation still load, and PDF requests return a localized unavailable result. Dedicated failure test and both supported-version suites pass. The upstream font LICENSE is preserved byte-for-byte, including one trailing space; it is the only diff-whitespace exception.

0.19.1 deployment verified: the final 66-file patch preserved all three saved stores, then a second backend restart loaded the versioned 0.19.1 UI. A retained completed report generated successfully and exposed Download, Open and Share commands. No observation or device control was activated. Both supported-version test suites and branch CI passed. Real phone acceptance remains pending.
