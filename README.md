# SoloForge

Open-source offline singleplayer game tuning, mod management, and trainer creation.

SoloForge is built with AI assistance from OpenAI Codex. The project attributes every public data source it indexes and keeps the product line clear: offline singleplayer games only.

## What Works Now

- static desktop-style MVP in `apps/desktop`
- normalized registry records in `registry`
- source attribution and license status tracking
- safety policy and source policy
- Python registry validator
- GitHub metadata importer scaffold
- GitHub Actions workflow for registry checks
- mock trainer-builder flow that models value scanning without attaching to real processes

Open the MVP directly:

```text
apps/desktop/index.html
```

No build step is required for the first milestone.

## Mission

SoloForge helps players customize offline singleplayer games they own. The project focuses on:

- discovering installed singleplayer games
- indexing public/open-source game-assist resources
- managing safe local tweaks such as configs, mods, saves, and profiles
- helping users build local trainers through transparent reviewable workflows
- documenting every source and license status

## Hard Rules

- Singleplayer and offline modes only.
- No multiplayer cheating.
- No anti-cheat bypasses.
- No stealth behavior.
- No proprietary database scraping.
- No bundled third-party tables or scripts unless the license permits redistribution.

## Repository Layout

```text
.github/workflows/       CI checks
apps/desktop/            static MVP app
docs/                    policies and architecture notes
packages/importers/      importer implementation notes and source
packages/registry-schema canonical registry schema
packages/safety-policy/  policy data
registry/games/          normalized game records
registry/sources/        source records
tests/                   Python tests
tools/                   validator, importer, app data generator
```

## Validate

```bash
python3 tools/validate_registry.py
python3 -m unittest discover -s tests
```

## Import Philosophy

SoloForge can integrate public sources in two modes:

- `metadata-only`: store source URL, game title, feature names, update timestamps, and attribution.
- `redistributable`: store actual files or structured cheat definitions only when the source license allows it.

Unknown license means `metadata-only`.

## License

SoloForge code is licensed under GPL-3.0-or-later.

Documentation and original registry metadata are licensed under CC BY 4.0 unless noted otherwise.

Third-party sources keep their original licenses.
