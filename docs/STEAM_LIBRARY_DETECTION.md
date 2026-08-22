# Steam Library Detection

SoloForge detects installed Steam games from local Steam metadata.

## Why Local Files

SteamDB is useful for human browsing, but it is not an API. Steam's official owned-games Web API requires a key, and profile/game privacy can block public access.

Local detection avoids those problems. It reads files Steam already keeps on the user's machine:

- `steamapps/libraryfolders.vdf`
- `steamapps/appmanifest_*.acf`

## Usage

Default scan:

```bash
python3 tools/scan_steam_libraries.py --pretty
```

Specific Steam root:

```bash
python3 tools/scan_steam_libraries.py --steam-root "C:\Program Files (x86)\Steam" --pretty
```

Search another drive or folder for Steam libraries:

```bash
python3 tools/scan_steam_libraries.py --scan-root "D:\SteamLibrary" --pretty
```

Write an import file for the desktop MVP:

```bash
python3 tools/scan_steam_libraries.py --pretty --output installed-games.json
```

Then open `apps/desktop/index.html`, go to `Installed`, and import that JSON file.

## Safety

The scanner only reads manifest files. It does not attach to game processes, inspect memory, or modify files.

Installed games that are not in the SoloForge registry are marked `requiresManualReview`.
