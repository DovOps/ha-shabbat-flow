# Implementation plan
1. Add sanitized live registry snapshots and a versioned HA Store for reviewed household intent.
2. Validate revisions, bindings and capabilities. Resolve names live; expose drift without mutating intent.
3. Build a multilingual House setup page, periodic refresh preserving unsaved edits, and explicit dated workspace creation.
4. Compile actual-room lighting/shared-area/HVAC preview profiles using existing pure engine. Keep drafts as snapshots.
5. Version all static paths; test both HA versions and standalone checks; package and deploy with rollback copy.
6. Verify live setup/preview presentation, record generic verification evidence, commit and merge to main.
