# Verification — stored PDF downloads (0.19.0)

- PDF-FR-001–003: real ReportLab generation tested for English/Hebrew reports and multi-day plans; embedded regular/bold fonts, vector charts, activity bands, per-zone hourly tables and saved owner reviews. Files are generated from canonical exported JSON / validated preview bundles. Cache identity includes app version, kind, language and complete source digest.
- PDF-FR-004–005: generation is lazy only. Tests cover persisted reuse after store restart, changed evidence rejected as stale, review-revision invalidation, expired/deleted run cleanup, renderer failure isolation, job queue bounds and duplicate generation. Private files use mode 0600. Preview cache expires after 24 hours; cache is capped at 40 files / 64 MiB.
- PDF-FR-006 / NFR-003: authenticated admin POST bridge only; no public static paths, external PDF provider or access token in links. Download transfers the stored bytes as a bounded JSON/base64 response, then exposes explicit Blob Download/Open/Share commands. Anonymous/non-admin and invalid IDs/languages are rejected.
- PDF-FR-007: preview compilation succeeds before rendering, input remains unchanged, and existing automation forecasts are informational.
- PDF-NFR-001: background generation with one renderer and two pending jobs maximum; cleanup scheduled independently from observer commits. File writes are atomic. Per-file cap 8 MiB, page cap 300. No device calls.
- Visual check: fictional mixed Hebrew/English room labels and feedback; seven-page Hebrew report inspected, including chart gaps, repeated table headers and active/inactive ordering. English multi-day plan reviewed. Embedded-font text geometry checked: only footers enter the bottom margin. Native print remains available for the HTML layout.
- Regression: 91 core and 64 JavaScript tests; 122 HA tests on each supported version (2026.8.2 and 2026.11.2); final PDF-specific checks repeated after renderer changes. EN/HE website builds and link checks pass.

Pending: installed-instance generation/download and actual iOS/Android Companion App Open/Share acceptance. Do not equate desktop verification with mobile acceptance. No automatic PDF pre-generation at study completion.

Hebrew units follow-up: classic Unicode bidi mirroring plus LTR unit marks correct `(°C)` and mixed numeric temperatures. Renderer and web tests cover parentheses, unit ordering and idempotence; regenerated Hebrew page visually confirmed.
