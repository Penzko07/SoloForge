# Trainer Builder

SoloForge should let players create local trainer definitions for offline singleplayer games they own.

## Current MVP

The desktop app includes a mock value scanner. It demonstrates:

- first scan
- changed-value scan
- candidate narrowing
- local draft creation
- offline-only warnings

It does not attach to a real process.

## Future Native Helper

The real scanner should live in a separate reviewed helper process.

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

## Trainer Definition Shape

```json
{
  "name": "Money Editor",
  "gameId": "example-game",
  "offlineOnly": true,
  "createdBy": "local-user",
  "storage": "local-only",
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
