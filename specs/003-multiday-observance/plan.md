
0.16.4: Apply explicit-use home defaults in immutable room, nap and meal model operations, with advanced custom availability preserved. Wire simple and advanced meal choices, describe exceptions inline and test multi-day/removal behavior. Keep manual Away and compiler conflict validation intact.

PDF font follow-up: change only the shared print body font stack to Arial/Tahoma/sans-serif. Compare identical fictional English/Hebrew text using the existing system font and Arial in Chrome Save as PDF; inspect font resources and render both pages. Preserve charts and report semantics. See docs/pdf-font-verification.md.

Deployment: ship source and generated HTML with a print-font CSS query marker, atomically replace only backed-up static assets and verify checksums. No Python version/restart is needed for this isolated patch; existing open pages need refreshing.
