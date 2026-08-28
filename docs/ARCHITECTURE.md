# Architecture

SoloForge starts as a registry-first app.

## Layers

```text
Desktop UI
  reads generated registry snapshot
  shows source attribution and safety status
  exposes the trainer-builder workflow
  receives native scan results when running inside a native app

Windows/Linux Electron App
  wraps the desktop UI in Chromium
  bundles registry metadata and a dependency-free Node scanner
  exposes a narrow IPC bridge for installed-game scanning
  exposes a Windows-only IPC bridge for user-guided memory scanning/writing

macOS App
  wraps the desktop UI in WebKit as a lightweight local build
  bundles scanner tools and registry metadata

Registry
  normalized JSON records for sources and games
  no executable third-party logic unless explicitly redistributable

Importers
  collect public metadata
  classify license and safety status
  never bypass access controls
  can match public/exported Steam libraries against registry metadata

Local Launcher Detection
  reads Steam, GOG, Ubisoft Connect, and EA App metadata when available
  matches installed store IDs and titles against registry metadata
  never attaches to processes or uploads private library data

Safety Policy
  blocks multiplayer and online contexts
  requires manual review for uncertain sources
  stays achievement-neutral and never spoofs platform achievements
```

## Trainer Builder

The Windows Electron build includes a native exact-value scan/narrow/write path.
It supports known registry games and custom singleplayer game drafts. Strictly
multiplayer targets are blocked. Browser and macOS builds keep a simulation
preview.

The native helper is separate from the UI and must keep these gates:

- explicit user confirmation
- offline singleplayer process selection
- source and trainer attribution
- backups for file writes
- no anti-cheat bypass behavior

## Registry Decisions

Unknown license means `metadata-only`.

Imported files are not redistributed until license review confirms that bundling is allowed.
