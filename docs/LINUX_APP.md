# Linux App

Linux is a supported secondary desktop target.

## Download From GitHub

Every push to `main` runs the `Validate` workflow. When it completes, open the workflow run and download the `SoloForge-linux` artifact.

The Linux artifact contains:

- a compressed `tar.gz` desktop package

Tagged releases also attach Linux builds to the GitHub Release page.

## Build On Linux

Requirements:

- Node.js 20 or newer
- Python 3.12 or newer

```bash
npm install
npm run dist:linux
```

The build output is written to:

```text
dist/
```

## Native Scanner

The Linux Electron app reads local launcher metadata from common locations such as:

- `~/.steam/steam`
- `~/.local/share/Steam`
- `~/GOG Games`
- mounted folders under `/mnt` and `/media`

Launcher support is metadata-only and best effort. The scanner does not sign in, upload private library data, attach to game processes, or modify game files.
