# Implementation Plan: multilingual preview

Branch: `001-preview-planner` | Date: 2026-11-17 | Spec: [spec.md](spec.md)

## Summary
Implement the deterministic compiler first and a local interactive dashboard consuming that compiler. No executor. Preserve the future HA integration/card boundary rather than selecting a live timer backend prematurely.

## Technical Context
Python 3.11+ stdlib (`zoneinfo`, JSON, HTTP server) for compiler and loopback development server; vanilla ES modules and CSS for a dependency-free preview. This small preview intentionally precedes a native TypeScript/Lit card: do not claim it is installed in HA. Python compiler can be reused by a future integration. Storage: explicit browser localStorage drafts only. Tests: unittest, node:test, browser interaction where available. Scale: at most 100 resources; 128 KiB input.

## Constitution Check
Repository hygiene: synthetic inputs only. Local/deterministic: no network client. Activation: absent. Multilingual: EN/HE catalogs and RTL before completion. Traceability: analysis.md. Reuse: research.md records Good Days comparison. No violations.

## Structure
`src/shabbat_flow/compiler.py`: schema validation, date resolution, resource union, events.
`src/shabbat_flow/server.py`: loopback-only sample UI and compile endpoint.
`src/shabbat_flow/web/`: HTML, CSS, modules, EN/HE catalogs.
`examples/`: fictional household and ordinary Shabbat plan.
`tests/`: compiler, transport, translations and UI logic checks.
`scripts/check_repository.py`: hygiene gate.

## Implementation decisions
Explicit timezone-aware anchors rather than an unverified calendar dependency. UTC arithmetic for elapsed offsets; local-zone conversion for display and fixed wall times. Frozen input digest excludes language. Bad input returns stable codes. JSON only; no YAML eval or arbitrary action code. API never persists input. Unknown routes and oversized/cross-origin requests are rejected. Close UI session safely without device effects.

## Milestones
1. Spec/research/contracts, then tests.
2. Compiler and fixture validation.
3. EN/HE interactive dashboard, local draft save/load/export.
4. Verification, hygiene review, checkpoint without commit/push.
Production discovery, HA installation and execution are separate reviewed features.
