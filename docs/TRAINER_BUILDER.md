# Trainer Builder

SoloForge should let players create local trainer definitions for offline singleplayer games they own.

## Current MVP

The Windows Electron app includes a native user-guided memory runtime. It supports:

- known registry games and custom singleplayer game names
- running-process selection
- explicit offline singleplayer confirmation
- first scan
- changed-value scan
- candidate narrowing
- selected-address writes
- local draft creation
- offline-only warnings
- strictly multiplayer blocking

Browser and macOS builds keep a preview simulation, because the real memory helper
is Windows-only.

## Native Helper

The scanner lives behind the Electron IPC bridge and calls a Windows helper script.

Required states:

- `notConnected`
- `awaitingUserAcknowledgement`
- `offlineProcessSelected`
- `scanning`
- `candidateReview`
- `draftSaved`
- `blocked`

Required blockers:

- multiplayer context
- known anti-cheat protected online context
- missing user acknowledgement
- unsupported platform
- unsigned or unreviewed helper build

The helper does not include fixed game offsets. For Persona 3 Reload, for example,
the user still scans the current Yen, HP, SP, or item value and narrows it after
changing that value in offline singleplayer play.

## Trainer Definition Shape

```json
{
  "name": "Money Editor",
  "gameId": "example-game",
  "offlineOnly": true,
  "singleplayerOnly": true,
  "multiplayerBlocked": true,
  "achievementCompatibility": "neutral-by-policy",
  "createdBy": "local-user",
  "storage": "local-only",
  "executionMode": "native-memory",
  "scan": {
    "valueType": "int32",
    "strategy": "exact-value-then-changed-value"
  },
  "actions": [
    {
      "type": "set-value",
      "label": "Set Money"
    },
    {
      "type": "freeze-value",
      "label": "Freeze Money"
    }
  ]
}
```
