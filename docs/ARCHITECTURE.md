# Architecture

SoloForge starts as a registry-first app.

## Layers

```text
Desktop UI
  reads generated registry snapshot
  shows source attribution and safety status
  exposes the trainer-builder workflow
  receives native scan results when running inside the macOS app

macOS App
  wraps the desktop UI in WebKit
  bundles scanner tools and registry metadata
  exposes a narrow native bridge for installed-game scanning

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

The first milestone includes a mock scanner so the user flow can be designed without attaching to a process.

A future native helper should be separate from the UI and must implement these gates:

- explicit user confirmation
- offline singleplayer process selection
- source and trainer attribution
- backups for file writes
- no anti-cheat bypass behavior

## Registry Decisions

Unknown license means `metadata-only`.

Imported files are not redistributed until license review confirms that bundling is allowed.
