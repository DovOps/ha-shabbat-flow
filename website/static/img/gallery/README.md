# Screenshot provenance

Original EN/HE pairs show the actual 0.16.0 local renderer with fictional fixtures, visually inspected before publication. No live household capture is used.

Run `python3 scripts/build_observation_example.py` and again with `--study`, then `PYTHONPATH=src python3 scripts/gallery_preview.py`. The loopback server at port 8773 serves production web sources, fictional room registry/settings and the repository sample plan. It never connects to HA.

- room-setup: `/household.html`, edit Room A; change language in the UI. Names are intentionally bilingual.
- planner, schedule, events: `/v2`, repository `examples/period-preview.json`, preview then capture each section in EN/HE. Dates are illustrative and are not genuine holiday predictions.
- climate-report: `/sample-climate.html?lang=en#sample-zone-first` (or he), generated standalone report.
- plan-observation: `/sample-plan.html?lang=en#sample-zone-first` (or he), generated plan-observation report.

Screens use decorative standalone icon fallbacks. HA-assigned icons render only with the HA frontend. Refresh both locale images and review all names, IDs and URLs for private data before publication. No browser chrome is included.

Settings EN/HE captures use the 0.16.2 production Settings renderer at `/settings.html` with fictional detected dependency statuses and disabled notification channels. No household screenshot, phone number, endpoint or device name is used. The fixture also offers 100 fictional climate zones and 2,000 activity signals for selection-performance verification; it refuses observation/settings writes.

0.16.4 home-overview and rooms-glance EN/HE captures: run `PYTHONPATH=src python3 scripts/gallery_preview.py --port 8774 --activity-examples`, open `/household.html` and change language using the UI. This opt-in fixture returns a fictional scheduled plan observation and observing climate study (fixed illustrative dates, not real collection). Rooms demonstrate Ready, Draft and Needs attention through actual setup validation. No browser draft is populated. Captures are unaltered browser crops of the production renderer; no household source or browser chrome is included.
