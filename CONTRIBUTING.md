# Contributing

SoloForge accepts contributions that support offline singleplayer game customization.

## Requirements

- Respect `docs/SAFETY_POLICY.md`.
- Respect `docs/SOURCE_POLICY.md`.
- Attribute every imported source.
- Mark unknown licenses as `metadata-only`.
- Do not submit multiplayer cheats, anti-cheat bypasses, DRM bypasses, or proprietary database dumps.
- Add or update registry records through the schema in `packages/registry-schema/src/schema.json`.
- Run validation before opening a pull request.

```bash
python3 tools/validate_registry.py
python3 -m unittest discover -s tests
```

## Source Review

Use `requiresManualReview` when a source is useful but license or safety status is unclear.

Use `blocked` for sources that primarily target multiplayer cheating, bypass access controls, or require proprietary scraping.
