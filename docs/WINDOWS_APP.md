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

## Native Trainer Runtime

The Windows app also includes a user-guided memory runtime:

- list running processes
- confirm offline singleplayer mode
- first exact-value scan
- changed-value narrowing
- selected-address write

This is not a fixed-offset trainer database. For Persona 3 Reload, SoloForge
knows the Steam AppID and `P3R.exe` process hint, but the user still scans the
current Yen, HP, SP, or item value in their own offline session.

## Safety Boundary

SoloForge only marks a detected game as eligible when the registry entry is offline singleplayer and multiplayer-blocked. Unknown games can still be used for local drafts, but strictly multiplayer games must remain blocked.

The app does not include anti-cheat bypasses, stealth injection, DRM bypasses, multiplayer support, or achievement spoofing.
