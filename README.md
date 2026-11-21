# Shabbat Flow

![ShabbatFlow logo](assets/logo.png)

Configurable Shabbat and Yom Tov household planning for Home Assistant.
Multilingual by design, with **English and Hebrew supported by default**, including right-to-left layout.

[מדריך התחלה בעברית](README.he.md) · [Checkpoint review](docs/checkpoint-001.md) · [Verification evidence](specs/001-preview-planner/verification.md)

**Current package: Shabbat Flow 0.20.0 — planning, observation and an explicitly armed lighting pilot.** Review a complete plan, qualify individual lighting controls, approve a subset and separately schedule it. Saving and previewing never control devices. Matching states are left unchanged. HVAC, fans and appliance execution remain unqualified and excluded. [Installation and limitations](docs/installation.md).

## Try the preview

Python 3.11+:

```sh
PYTHONPATH=src python3 -m shabbat_flow.server
```

Open **http://127.0.0.1:8765**. Select rooms and meals, adjust independent HVAC/lighting timings, switch English/עברית, and preview the schedule. Save/load/delete a draft explicitly in your browser. Exporting downloads your inputs and computed preview; keep any real configuration private. The server does not store submissions. Stop with Ctrl+C.

The new **[multi-day preview](http://127.0.0.1:8765/v2)** adds separate sleeping/recreation windows, configurable sleep profiles, per-day meals, availability windows, explicit heating/cooling, shared-load conflict checks and a combined timeline. It uses separate v2 draft storage. Adding/removing days requires supplying the corresponding dated anchors and adjusting period coverage. The default view uses day tabs, room tiles and meal choices, with a reviewed copy-previous-day action. Optional bedroom timing sliders keep HVAC and lights independent. Calendar, interval/group editors and JSON are under Advanced setup. Browser visual/interaction verification of v2 is pending.

Calendar inputs are deliberately illustrative. The original v1 preview covers a single ordinary Friday/Saturday and is not a full operational schedule. The v1 compiler is unchanged. V2 accepts supplied multi-day periods and explicit HVAC settings but the standalone server has no live HA calendar data. Neither host provides production execution, automatic v1 migration, feedback storage or boiler automation management. It cannot activate a plan.

## Develop with a coding agent

Shabbat Flow is designed for **LLM/coding-agent-assisted, specification-driven development**. Start your agent at the repository root and explicitly ask it to read [AGENTS.md](AGENTS.md), then the constitution and relevant feature specs. Update FRs/NFRs, acceptance criteria, plans and tasks before implementation; keep evidence and status current afterward. Human-only contributions follow the same process.

The [developer guide](website/content/en/contributing.md) includes the workflow and a copyable starter prompt; the [Hebrew guide](website/content/he/contributing.md) covers the same process. Agent output still requires human review, and deployment/device control needs separate authorization.

## Requirements and development

- [Constitution](.specify/memory/constitution.md)
- [Feature specification](specs/001-preview-planner/spec.md), [plan](specs/001-preview-planner/plan.md), [tasks](specs/001-preview-planner/tasks.md)
- [Dependency decision gate](docs/dependencies.md): no adopted third-party HA integration or runtime design
- [Reuse research](specs/001-preview-planner/research.md)
- [Spec Kit workflow and provenance](docs/spec-kit.md)
- [Extensible groups and room uses](specs/002-extensible-schedule-groups/spec.md) (planned)
- [Multi-day observance planning](specs/003-multiday-observance/spec.md) (planned)
- [Feedback and improvement loop](specs/004-feedback-loop/spec.md) (planned)
- [Optional MCP/chat interface](specs/005-chat-interface/spec.md) (planned)
- [Next implementation plan](specs/002-extensible-schedule-groups/plan.md)
- [Product roadmap](docs/roadmap.md)

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
node --test tests/web.test.mjs
python3 scripts/check_repository.py
```

The preview uses Python standard libraries and browser-native modules. Node is a test tool only. No package install is needed. The optional HA package is built with `python3 scripts/build_ha.py --check --zip`; see [feature 006](specs/006-installable-preview/spec.md).

## Contributor configuration boundary

Keep real household/family details, addresses, credentials, device inventory and histories outside this repository. Generalize contributions into logical rooms/resources and fictional examples; each installer supplies their own private mappings. See [AGENTS.md](AGENTS.md). Do not copy adjacent local files into this project. Hygiene checks supplement, not replace, review.

All UI strings belong in catalogs; add language metadata and tests when adding languages. Translation review by native speakers is welcome. Current screenshots and verification are development evidence, not HA compatibility claims.

## License and attribution

The project license is pending owner selection before public release. No blanket open-source license is asserted yet. Vendored official Spec Kit scaffolding retains its [upstream license](docs/vendor/spec-kit-LICENSE). The logo was generated for this project using an image-generation tool. Research references do not imply affiliation with their authors or with Home Assistant.

Optional HA label filters simplify room setup; see [Setup tips](docs/setup-tips.md).

Preview 0.7.1 adds bathroom daylight/night policies, room night/morning presets, meal lighting/HVAC groups, and optional final-observance shutoff (off by default). Existing workspace exports remain snapshots; create a new workspace after changing house setup.

## Website and documentation

The brochure, EN/HE guides and generated specification reference live in `website/`. Run `npm ci`, `npm run build`, `npm run check` and `npm run serve` there to preview at `http://localhost:3000/ha-shabbat-flow/`. See [website maintenance and Pages setup](docs/website.md). Public publication is owner-enabled; the integration's current device-control and validation boundaries remain explicit.
