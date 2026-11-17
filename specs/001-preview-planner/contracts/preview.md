# Preview API

Local development only. `GET /api/example` → `{config, plan}` synthetic fixture.
`GET /api/i18n` → `{en, he}` bundled catalogs.
`POST /api/preview`, application/json, ≤128 KiB: `{config, plan}` → 200 `{preview_only:true, digest, events, preparation_at}`.
400 → `{error:CODE}`, with no echoed payload/exception; 413 oversized; 403 cross-origin or wrong Host; 404 unknown route. No write, auth-token, device action or activation API. Server listens only on 127.0.0.1.

Static routes are allowlisted. Draft persistence is browser-only on explicit Save. Export bundles configuration, plan and preview and must show a privacy notice. Invalid or unsupported browser drafts never replace the current valid form state.
