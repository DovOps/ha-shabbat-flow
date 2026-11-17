# Quickstart

Python 3.11+ and Node 18+ (Node for tests only).

```sh
PYTHONPATH=src python3 -m shabbat_flow.server
```

Open http://127.0.0.1:8765. Use only the fictional sample for this checkpoint. Choose rooms/meals, adjust separate offsets, preview, switch English/Hebrew, save/load a browser-local draft and export JSON. No HA server or credentials needed. Stop with Ctrl+C.

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
node --test tests/web.test.mjs
python3 scripts/check_repository.py
```

Drafts live only in this browser origin; use Delete saved draft to remove them. Downloads are not automatically private. Never commit real-house exports. This dev server is not for LAN hosting or production.
