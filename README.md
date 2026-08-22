# SoloForge

Open-source offline singleplayer game tuning, mod management, and trainer creation.

SoloForge is built with AI assistance from OpenAI Codex. The project attributes every public data source it indexes and keeps the product line clear: offline singleplayer games only.

## What Works Now

- static desktop-style web MVP in `apps/desktop`
- normalized registry records in `registry`
- source attribution and license status tracking
- safety policy and source policy
- Python registry validator
- local launcher scanner for Steam plus experimental GOG, Ubisoft Connect, and EA App metadata
- local HTTP server for Chrome/browser testing
- GitHub API publish helper for machines where normal `git push` has no HTTPS credentials
- GitHub metadata importer scaffold
- GitHub Actions workflow for registry checks
- mock trainer-builder flow that models value scanning without attaching to real processes

SoloForge is not a signed native installer yet. For now it is a local web app
plus command-line tools. A packaged desktop build is a later milestone.

Open the MVP directly:

```text
apps/desktop/index.html
```

Or serve it locally for Chrome:

```bash
python3 tools/serve_desktop_app.py --open
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

## Detect Installed Games

SoloForge can scan local launcher metadata without SteamDB, launcher logins, or Web API keys:

```bash
python3 tools/scan_installed_games.py --pretty --output installed-games.json
```

Scan one launcher:

```bash
python3 tools/scan_installed_games.py --launcher steam --pretty
python3 tools/scan_installed_games.py --launcher gog --pretty
python3 tools/scan_installed_games.py --launcher ubisoft --pretty
python3 tools/scan_installed_games.py --launcher ea --pretty
```

If a launcher is installed in a custom location or on another drive:

```bash
python3 tools/scan_steam_libraries.py --steam-root "C:\Program Files (x86)\Steam" --pretty
python3 tools/scan_installed_games.py --gog-root "D:\GOG Games" --pretty
python3 tools/scan_installed_games.py --ubisoft-root "D:\Ubisoft Games" --pretty
python3 tools/scan_installed_games.py --ea-root "D:\EA Games" --pretty
```

Then open `apps/desktop/index.html`, go to `Installed`, and import the generated JSON file.

Steam detection is the most complete scanner. GOG, Ubisoft Connect, and EA App
support is best-effort metadata parsing and should be expanded as contributors
verify more real launcher formats.

## Publish to GitHub

Normal `git push` is still recommended. If HTTPS credentials are missing, use a
temporary token:

```bash
export SOLOFORGE_GITHUB_TOKEN="github_pat_..."
python3 tools/publish_to_github.py --repo Penzko07/SoloForge --branch main
```

The helper publishes the committed `HEAD` through GitHub's Git API and does not
store the token.

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
