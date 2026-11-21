# Checkpoint 026 — permanent room fans (0.19.2)

Feature 017 persists optional fan assignments independently of lighting and HVAC. Native fan and switch controls use the existing optional label filters and explicit ownership checks. Migration adds empty fan arrays; no automatic household mapping. New snapshots include semantic fan loads with no implicit windows; existing dated plans stay unchanged.

Verification: 91 core / 65 JavaScript tests and 124 HA tests on both supported versions. Added fan selection filtering, migration without source mutation, saved-store reload, domain rejection, duplicate-role rejection, changed area detection, fan-only room snapshots, no implicit fan events and explicit track-only On/Off windows. EN/HE fictional room editors visually inspected with correct checkbox direction and localized guidance. Existing icon renderer is reused; standalone preview uses fallback symbols. Website guides updated in both languages. No new dependency or device control.

Deployment: pending. Household fan selections remain for the owner to review; no real household names or device mappings are committed.
