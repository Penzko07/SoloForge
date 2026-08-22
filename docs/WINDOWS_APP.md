# Windows App

Windows is the primary desktop target for SoloForge.

## Download From GitHub

Every push to `main` runs the `Validate` workflow. When it completes, open the workflow run and download the `SoloForge-windows` artifact.

The Windows artifact contains:

- an NSIS installer `.exe`
- a portable `.exe`

Tagged releases also attach the Windows builds to the GitHub Release page.

## Build On Windows

Requirements:

- Node.js 20 or newer
- Python 3.12 or newer

```powershell
npm install
npm run dist:win
```

The build output is written to:

```text
dist/
```

## Native Scanner

The Electron app includes a dependency-free Node scanner. It reads local launcher metadata from common Windows locations and mounted drives for:

- Steam
- GOG Galaxy / GOG Games
- Ubisoft Connect
- EA App

It does not require Python on the gaming PC.

## Safety Boundary

SoloForge only marks a detected game as eligible when the registry entry is offline singleplayer and multiplayer-blocked. Unknown games can still be used for local drafts, but strictly multiplayer games must remain blocked.

The app does not attach to processes yet. The current trainer builder stores local drafts for the reviewed helper that will come later.
