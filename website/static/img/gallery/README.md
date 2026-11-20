# Screenshot provenance

All current EN/HE pairs show the actual 0.16.0 local renderer with fictional fixtures, visually inspected before publication. No live household capture is used.

Run `python3 scripts/build_observation_example.py` and again with `--study`, then `PYTHONPATH=src python3 scripts/gallery_preview.py`. The loopback server at port 8771 serves production web sources, fictional room registry/settings and the repository sample plan. It never connects to HA.

- room-setup: `/household.html`, edit Room A; change language in the UI. Names are intentionally bilingual.
- planner, schedule, events: `/v2`, repository `examples/period-preview.json`, preview then capture each section in EN/HE. Dates are illustrative and are not genuine holiday predictions.
- climate-report: `/sample-climate.html?lang=en#sample-zone-first` (or he), generated standalone report.
- plan-observation: `/sample-plan.html?lang=en#sample-zone-first` (or he), generated plan-observation report.

Screens use decorative standalone icon fallbacks. HA-assigned icons render only with the HA frontend. Refresh both locale images and review all names, IDs and URLs for private data before publication. No browser chrome is included.
