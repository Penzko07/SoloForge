# Custom Cheat Drafts

SoloForge should let players make their own local cheat definitions for offline singleplayer games they own.

## Current Behavior

The desktop app supports local draft creation:

- choose a known registry game or enter a custom singleplayer game name
- choose a value type
- run a mock first scan
- narrow candidates with a changed value
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

Real memory editing should live in a separate reviewed helper. Before that helper can write values, it must support:

- explicit user confirmation
- offline singleplayer process selection
- save/config backups before file writes
- visible attribution for imported sources
- a blocked state for multiplayer and online contexts

SoloForge must not include anti-cheat bypasses, DRM bypasses, stealth behavior, or achievement spoofing.
