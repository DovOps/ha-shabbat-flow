# Feature 016 — Stored PDF downloads

Status: implemented and locally verified; deployment and phone acceptance pending.

## Problem
Native browser printing does not reliably open in the HA Companion App. Reports need an actual PDF stored on the HA host and a download command, independent of the mobile print dialog.

## Functional requirements
- PDF-FR-001: Reports and observation pages offer Generate / Download PDF, separately from browser Print. Completed plan observations and climate studies support stored English and Hebrew PDFs with the logo, summary tables, thermal charts, activity bands and saved feedback. Partial reports are explicitly marked.
- PDF-FR-002: Store generated files privately on the HA configuration disk, outside public www/static paths. Download through an authenticated administrator endpoint; do not expose permanent public or bearer-token URLs.
- PDF-FR-003: Cache by run ID, language, report-data digest, review revision and renderer version. Changed samples or feedback invalidate the prior artifact. The PDF displays generation time and period boundaries.
- PDF-FR-004: Generate lazily on explicit demand from saved JSON, then reuse the artifact while its source digest is unchanged. Do not generate at study completion. Evicted artifacts regenerate on the next request. A failed PDF must not fail or interrupt observation. Show pending, ready and failed states with retry.
- PDF-FR-005: Existing retained studies can generate PDFs without rerunning observations. Deleting/expiring a retained run removes its cached PDF; clearing feedback invalidates any PDF containing that feedback.
- PDF-FR-006: Authenticated mobile download/open uses the existing HA connection. Keep the report HTML and JSON available if file opening fails. Do not claim Companion App compatibility until tested on a real phone.
- PDF-FR-007: Plan-preview PDF downloads use the exact submitted preview snapshot and schedule, not current mutable room settings. Their short-lived cache is distinct from observed-period reports. Show preview versus observation clearly.

## Nonfunctional requirements
- PDF-NFR-001: Rendering and disk writes run off the HA event loop; serialize/bound rendering jobs, file size and cache capacity. Atomic replacement prevents serving incomplete files. Reject unknown IDs, unsupported languages and arbitrary paths.
- PDF-NFR-002: Embed licensed bundled fonts; support Hebrew RTL and mixed Hebrew/English entity names without reversing identifiers. Parentheses must mirror correctly; Celsius/Fahrenheit symbols and their numerical values stay left-to-right inside Hebrew sentences and table headings, on screen and in PDFs. Prefer vector charts/text over full-page raster screenshots. No remote fonts, assets or cloud rendering service.
- PDF-NFR-003: Preserve authorization across generation and download; test anonymous/non-admin denial, path traversal, stale cache, restart recovery, clear-review invalidation and retention cleanup. Do not put access tokens in logs or filenames.
- PDF-NFR-004: Validate output text/page counts and visual rendering in both languages, long room labels, large studies and empty/partial evidence. Avoid any device calls.
- PDF-NFR-005: Pin approved direct dependencies and test both supported HA versions; retain a working non-PDF report path when rendering is unavailable.

## Acceptance
From a completed study, request a PDF, see generation status, download a real application/pdf file from HA without window.print, reopen it after HA restart, save revised feedback and receive a refreshed file. Verify actual iOS/Android Companion App behavior separately.
