# SoloForge Source Policy

SoloForge integrates public game-assist data with attribution and license awareness.

## Import Modes

### metadata-only

Use this mode when the source is public but redistribution is unclear or not allowed.

Allowed fields:

- source name
- source URL
- repository or forum URL
- game title
- platform tags
- feature names
- author names when public
- last seen timestamp
- license status

Do not store executable trainer logic, scripts, binaries, or full copied posts in this mode.

### redistributable

Use this mode only when the source license permits redistribution.

Allowed fields:

- all metadata-only fields
- original files, if license-compatible
- parsed structured cheat definitions
- local mirrors of source files with attribution

## Required Attribution

Each imported source must include:

- source name
- source URL
- author or organization, when available
- license or `unknown`
- import mode
- date first added
- date last checked

## Rejected Sources

Do not import from:

- proprietary trainer databases that do not permit scraping or redistribution
- leaked databases
- paid-only content without permission
- sources primarily focused on multiplayer cheating
- sources that require bypassing access controls

## License Handling

Unknown license means metadata-only by default.

Redistribution requires an explicit compatible license or direct permission from the rights holder.
