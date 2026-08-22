# Implementation Notes

This document records how the current SoloForge MVP was built.

## Repository

The repository starts with policies, registry records, importers, tests, and a static desktop UI.

Key paths:

- `apps/desktop`: browser UI
- `apps/macos`: native macOS wrapper
- `registry`: normalized source and game metadata
- `tools`: scanners, importers, publishing, and build scripts
- `tests`: unit tests for registry, scanners, and importers
- `.github/workflows/validate.yml`: continuous validation

## Desktop UI

The UI reads `apps/desktop/app-data.js`, which is generated from `registry` by:

```bash
python3 tools/update_app_data.py
```

The UI supports:

- registry overview
- source attribution
- installed-game scan import
- native macOS scan bridge
- mock trainer-builder flow
- offline/singleplayer safety messaging

## Native macOS App

The macOS app is a small Objective-C AppKit/WebKit shell. It loads `desktop/index.html` from the app bundle and exposes one native bridge action for scanning installed launcher metadata.

Build command:

```bash
bash tools/build_macos_app.sh
```

## Launcher Detection

`tools/scan_installed_games.py` reads local metadata from Steam, GOG, Ubisoft Connect, and EA App locations. It can also inspect common launcher folders on mounted drives with:

```bash
python3 tools/scan_installed_games.py --all-drives --pretty
```

The scanner never logs in, queries private APIs, attaches to game processes, or modifies files.

## Steam Library Coverage

`tools/import_steam_library.py` matches public/exported Steam library data against the SoloForge registry. It reports which owned games already have offline singleplayer metadata and which need review.

## Cheat Data

Current cheat data is metadata-only unless the source license clearly permits redistribution. Unknown or mixed licenses stay metadata-only.

This means SoloForge can show:

- source URL
- feature name
- store IDs
- safety status
- attribution text

It does not bundle third-party cheat tables until license and safety review allow it.

## GitHub Publishing

Normal `git push` is preferred. When local HTTPS credentials are unavailable, `tools/publish_to_github.py` can publish committed `HEAD` using a temporary GitHub token from `SOLOFORGE_GITHUB_TOKEN` or `GITHUB_TOKEN`.
