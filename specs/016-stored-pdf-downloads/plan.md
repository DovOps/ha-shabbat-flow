# Implementation plan

1. Confirm renderer dependency choice and mobile authenticated file-delivery design.
2. Prototype English/Hebrew branded rendering with fictional report data and existing fonts. Compare charts/table coverage against the HTML report before adoption.
3. Add a bounded private artifact store, digest/version cache and invalidation tied to report/review retention.
4. Add authenticated generation/status/download APIs, executor-backed rendering and restart-safe file handling.
5. Replace the primary PDF action with stored-file generation/download; retain browser Print as an alternative. Provide localized progress/errors.
6. Add plan-preview snapshot PDF path and optional completion preparation without delaying observation completion.
7. Test backend auth/concurrency/cache and EN/HE visual output; run regressions and website updates, then deploy an approved renderer package. Real phone acceptance is required.

## Proposed dependency decision
Recommend ReportLab 5.1.0 with its bidi/shaping extras for embedded-font vector PDF rendering. Runtime transitives include Pillow, charset-normalizer, rlbidi and uharfbuzz; resolve and record exact compatible versions before adoption. ReportLab is BSD licensed. Its RTL implementation needs a visual compatibility spike; no claim of exact browser layout equivalence.

Alternatives: server-side Chromium preserves the existing HTML layout but adds a browser binary and materially greater installation/memory cost; retaining native print adds no dependency but does not solve mobile generation. Uploading PDFs generated on a desktop is not an independent mobile workflow.

No new dependency or renderer has been added. Repository dependency rules require owner review before adopting a library.
