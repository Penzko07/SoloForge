# SoloForge Safety Policy

SoloForge is for offline singleplayer game customization only.

## Allowed

- Singleplayer game config changes.
- Savegame backup and restore.
- Local mod enable/disable workflows.
- Memory scanning for games owned by the user, when played offline.
- Trainer definitions for offline singleplayer modes.
- Accessibility-style assists such as speed, difficulty, resource, and grind reduction tools.

## Not Allowed

- Multiplayer cheats.
- Online economy manipulation.
- Leaderboard, matchmaking, or PvP manipulation.
- Anti-cheat bypasses.
- Kernel drivers for cheat evasion.
- Stealth injection.
- DRM bypasses.
- Scraping proprietary trainer implementation databases.

## App Behavior Requirements

SoloForge should:

- label every feature as `offlineOnly`
- warn before attaching to a running process
- block known multiplayer-only titles and modes
- show source attribution before enabling imported trainer content
- default to backups before writing configs or saves
- make local user-created trainers private unless the user explicitly exports them

## Process Attachment Rules

The trainer builder may attach to a process only after the user confirms:

- the game is owned by the user
- the current mode is offline singleplayer
- no anti-cheat protected online session is active

When SoloForge cannot determine safety, it must choose `requiresManualReview`.
