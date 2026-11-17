# ShabbatFlow

![ShabbatFlow logo](assets/logo.png)

Configurable Shabbat and Yom Tov household planning for Home Assistant.
Multilingual by design, with **English and Hebrew supported by default**, including right-to-left layout.

[מדריך התחלה בעברית](README.he.md) · [Checkpoint review](docs/checkpoint-001.md) · [Verification evidence](specs/001-preview-planner/verification.md)

**Current checkpoint: local preview prototype.** No HA connection, device control, production integration installation or automatic zmanim calculation. Only fictional sample configuration is included. The full product scope is in [the roadmap](docs/roadmap.md).

## Try the preview

Python 3.11+:

```sh
PYTHONPATH=src python3 -m shabbat_flow.server
```

Open **http://127.0.0.1:8765**. Select rooms and meals, adjust independent HVAC/lighting timings, switch English/עברית, and preview the schedule. Save/load/delete a draft explicitly in your browser. Exporting downloads your inputs and computed preview; keep any real configuration private. The server does not store submissions. Stop with Ctrl+C.

Calendar inputs are deliberately illustrative. This preview covers a single ordinary Friday/Saturday and is not a full operational schedule. Temperature settings, per-room HVAC-off, naps, live HA calendar data, multi-day holidays, outdoor extensions and boiler automation management remain future work. It cannot activate a plan.

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

The preview uses Python standard libraries and browser-native modules. Node is a test tool only. No package install is needed. HA packaging and provider integration will be a separate reviewed feature.

## Contributor configuration boundary

Keep real household/family details, addresses, credentials, device inventory and histories outside this repository. Generalize contributions into logical rooms/resources and fictional examples; each installer supplies their own private mappings. See [AGENTS.md](AGENTS.md). Do not copy adjacent local files into this project. Hygiene checks supplement, not replace, review.

All UI strings belong in catalogs; add language metadata and tests when adding languages. Translation review by native speakers is welcome. Current screenshots and verification are development evidence, not HA compatibility claims.

## License and attribution

The project license is pending owner selection before public release. No blanket open-source license is asserted yet. Vendored official Spec Kit scaffolding retains its [upstream license](docs/vendor/spec-kit-LICENSE). The logo was generated for this project using an image-generation tool. Research references do not imply affiliation with their authors or with Home Assistant.
