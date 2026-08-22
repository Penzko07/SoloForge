# Steam Library Import

SoloForge can match a Steam library against the local registry and report which games already have offline singleplayer tool metadata.

## Public Profile Lookup

For a public Steam profile:

```bash
python3 tools/import_steam_library.py --steam-id 76561198108903649 --pretty --output steam-library-coverage.json
```

This uses Steam Community's public games XML page. It works only when the profile and game details are public and the network can reach Steam.

## SteamDB Calculator Export

If SteamDB is easier to view in a browser, save the calculator page HTML and import it:

```bash
python3 tools/import_steam_library.py --steamdb-html steamdb-calculator.html --pretty --output steam-library-coverage.json
```

## Installed Scan Input

You can also import a SoloForge installed-game scan:

```bash
python3 tools/scan_installed_games.py --all-drives --pretty --output installed-games.json
python3 tools/import_steam_library.py --scan-json installed-games.json --pretty --output steam-library-coverage.json
```

## Matching Rules

SoloForge matches Steam games by:

- Steam AppID first
- normalized title second

Only registry games with `singleplayerOnly=true`, `offlineOnly=true`, and `multiplayerBlocked=true` are marked `singleplayerEligible`.

The importer does not download or redistribute cheat tables. It attaches existing SoloForge metadata such as public source links, feature names, safety status, and attribution.

## Import Into The App

Open the `Installed` view and choose `Import scan`. The app accepts both:

- `installed-games.json` from `tools/scan_installed_games.py`
- `steam-library-coverage.json` from `tools/import_steam_library.py`
