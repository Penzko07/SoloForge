# SoloForge

Open-source offline singleplayer game tuning, mod management, and trainer creation.

SoloForge is built with AI assistance from OpenAI Codex. The project attributes every public data source it indexes and keeps the product line clear: offline singleplayer games only.

## What Works Now

- Windows-focused Electron desktop app packaging
- Linux Electron desktop app packaging
- static desktop-style web MVP in `apps/desktop`
- normalized registry records in `registry`
- source attribution and license status tracking
- safety policy and source policy
- Python registry validator
- local launcher scanner for Steam plus experimental GOG, Ubisoft Connect, and EA App metadata
- dependency-free Electron scanner for Windows/Linux installed-game detection
- native macOS app wrapper with a local scanner bridge
- Steam library coverage importer for public/exported library data
- local HTTP server for Chrome/browser testing
- GitHub API publish helper for machines where normal `git push` has no HTTPS credentials
- GitHub metadata importer scaffold
- GitHub Actions workflow for registry checks and desktop package artifacts
- Windows native trainer runtime for user-guided memory scan/narrow/write flows
- browser/macOS trainer-builder preview for custom singleplayer drafts

SoloForge is not code-signed by a commercial certificate yet. Windows and Linux
packages are built by GitHub Actions. The original browser UI and local macOS
wrapper still work.

## Download The App

Windows is the primary target.

On GitHub, open the latest successful `Validate` workflow run and download:

- `SoloForge-windows`: Windows installer and portable executable
- `SoloForge-linux`: Linux tar.gz package
- `SoloForge-macos`: lightweight macOS app bundle

Tagged releases also publish Windows and Linux assets on the Release page.

Build locally on Windows:

```powershell
npm install
npm run dist:win
```

Build locally on Linux:

```bash
npm install
npm run dist:linux
```

Build the macOS app:

```bash
bash tools/build_macos_app.sh
open build/macos/SoloForge.app
```

Open the browser UI directly:

```text
apps/desktop/index.html
```

Or serve it locally for Chrome:

```bash
python3 tools/serve_desktop_app.py --open
```

See `docs/WINDOWS_APP.md`, `docs/LINUX_APP.md`, and `docs/RUNNING_LOCALLY.md`.

## Mission

SoloForge helps players customize offline singleplayer games they own. The project focuses on:

- discovering installed singleplayer games
- indexing public/open-source game-assist resources
- managing safe local tweaks such as configs, mods, saves, and profiles
- helping users build local trainers and custom singleplayer drafts through transparent reviewable workflows
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
apps/electron/           Windows/Linux app shell and Node scanner
apps/macos/              lightweight macOS app shell
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

Search common launcher folders on mounted drives:

```bash
python3 tools/scan_installed_games.py --all-drives --pretty --output installed-games.json
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
python3 tools/scan_installed_games.py --drive-root "D:\" --pretty
```

Then open `apps/desktop/index.html`, go to `Installed`, and import the generated JSON file.

The Windows/Linux Electron app can run its own installed-game scanner from the
`Installed` view with `Scan this PC`.

Steam detection is the most complete scanner. GOG, Ubisoft Connect, and EA App
support is best-effort metadata parsing and should be expanded as contributors
verify more real launcher formats. The all-drives mode checks common launcher
folders on mounted drives; it does not blindly crawl every file on the system.

## Match a Steam Library

For a public Steam profile:

```bash
python3 tools/import_steam_library.py --steam-id 76561198108903649 --pretty --output steam-library-coverage.json
```

If SteamDB is open in a browser, save the calculator HTML and import it:

```bash
python3 tools/import_steam_library.py --steamdb-html steamdb-calculator.html --pretty --output steam-library-coverage.json
```

The importer matches library games to existing SoloForge registry metadata. It
does not download or bundle third-party cheat tables.

## Custom Singleplayer Cheats

The builder can save local draft cheat definitions for:

- known registry games
- custom game names entered by the user

Drafts are always marked offline-only and singleplayer-only. If a game is
strictly multiplayer, the builder blocks the draft.

The Windows Electron app can list running processes, perform exact-value scans,
narrow candidate addresses after an in-game value changes, and write the chosen
value. Browser and macOS builds keep a preview simulation so the workflow can be
reviewed without attaching to a process.

The native runtime is user-guided. It does not include fixed offsets, anti-cheat
bypasses, stealth behavior, or multiplayer support.

## Achievements

SoloForge is achievement-neutral. It does not spoof achievements, call Steam
achievement APIs, or bypass game logic that disables achievements. If a game
naturally allows achievements while local singleplayer tools are active,
SoloForge does not block that.

See `docs/ACHIEVEMENTS.md`.

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
npm run check:js
bash tools/build_macos_app.sh
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
