# Local Launcher Detection

SoloForge detects installed games from local launcher metadata.

## Why Local Files

SteamDB is useful for human browsing, but it is not an API. Steam's official owned-games Web API requires a key, and profile/game privacy can block public access.

Local detection avoids those problems. It reads metadata files launchers already keep on the user's machine.

Steam support reads:

- `steamapps/libraryfolders.vdf`
- `steamapps/appmanifest_*.acf`

Experimental GOG support reads:

- `goggame-*.info`
- `galaxy-2.0.db` rows when recognizable title/path columns exist

Experimental Ubisoft Connect support reads recognizable local manifest/state text files such as:

- `uplay_install.state`
- install or manifest JSON/YAML files

Experimental EA App support reads recognizable local install metadata such as:

- `__Installer/installerdata.xml`
- install or manifest JSON files

## Usage

Default scan for all supported launchers:

```bash
python3 tools/scan_installed_games.py --pretty
```

Scan one launcher:

```bash
python3 tools/scan_installed_games.py --launcher steam --pretty
python3 tools/scan_installed_games.py --launcher gog --pretty
python3 tools/scan_installed_games.py --launcher ubisoft --pretty
python3 tools/scan_installed_games.py --launcher ea --pretty
```

Specific roots:

```bash
python3 tools/scan_installed_games.py --steam-root "C:\Program Files (x86)\Steam" --pretty
python3 tools/scan_installed_games.py --gog-root "D:\GOG Games" --pretty
python3 tools/scan_installed_games.py --ubisoft-root "D:\Ubisoft Games" --pretty
python3 tools/scan_installed_games.py --ea-root "D:\EA Games" --pretty
```

Write an import file for the desktop MVP:

```bash
python3 tools/scan_installed_games.py --pretty --output installed-games.json
```

Then open `apps/desktop/index.html`, go to `Installed`, and import that JSON file.

The legacy Steam-only command still works:

```bash
python3 tools/scan_steam_libraries.py --pretty
```

## Safety

The scanner only reads manifest files. It does not attach to game processes, inspect memory, or modify files.

Installed games that are not in the SoloForge registry are marked `requiresManualReview`.

Steam detection is the most complete scanner today. GOG, Ubisoft Connect, and
EA App support are best-effort until contributors verify more real launcher
metadata formats.
