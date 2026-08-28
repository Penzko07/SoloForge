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
