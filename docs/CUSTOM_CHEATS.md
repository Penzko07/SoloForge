# Custom Cheat Drafts

SoloForge should let players make their own local cheat definitions for offline singleplayer games they own.

## Current Behavior

The desktop app supports local draft creation. On Windows, the Electron app can
also run a native exact-value memory workflow:

- choose a known registry game or enter a custom singleplayer game name
- choose the running game process
- confirm offline singleplayer mode
- choose a value type
- run a first scan
- narrow candidates with a changed value
- write the selected changed value on Windows
- save a local draft in browser/app storage

Drafts are marked:

- `offlineOnly`
- `singleplayerOnly`
- `multiplayerBlocked`
- `achievementCompatibility: neutral-by-policy`

## Multiplayer Block

The builder includes a `Strictly multiplayer` blocker. When enabled, the draft cannot be saved.

This is intentionally simple: if the game is built only for multiplayer or online competitive play, SoloForge should not help build or run cheats for it.

## Future Native Helper

The current Windows helper is intentionally narrow. Future versions should add:

- better process-to-game matching
- save/config backups before file writes
- visible attribution for imported sources
- a blocked state for multiplayer and online contexts

SoloForge must not include anti-cheat bypasses, DRM bypasses, stealth behavior, or achievement spoofing.
