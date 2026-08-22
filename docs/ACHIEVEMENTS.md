# Achievements

SoloForge is achievement-neutral by policy.

That means SoloForge should not:

- call Steam achievement APIs
- spoof or unlock achievements directly
- bypass game logic that disables achievements
- patch platform, DRM, or anti-cheat code to preserve achievements

## Are Achievements Still Possible?

Sometimes, yes. Many singleplayer trainers or local config/save changes do not automatically disable Steam achievements. In those games, achievements may continue to unlock normally.

Sometimes, no. Some games deliberately disable achievements when mods, console commands, debug flags, or changed save files are detected.

SoloForge should preserve achievements only when the game naturally allows it. It should not add bypasses whose purpose is to override achievement-disabled states.

## App Behavior

SoloForge labels compatible records as `achievementCompatibility: neutral-by-policy` when they are offline singleplayer registry matches.

Future executable trainer support should show a warning before enabling a tool if a source or game is known to disable achievements.
