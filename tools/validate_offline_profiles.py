#!/usr/bin/env python3
"""Validate local-only offline trainer profile metadata."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "registry" / "offline-profiles"
REQUIRED = {"id", "name", "game", "safety", "features"}
REQUIRED_SAFETY = {"singleplayerOnly", "offlineOnly", "multiplayerBlocked"}


def main() -> int:
    profiles = sorted(PROFILE_DIR.glob("*.json"))
    if not profiles:
        raise SystemExit("No offline profiles found")

    profile_count = 0
    for path in profiles:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else [payload]
        for record in records:
            profile_count += 1
            missing = REQUIRED - record.keys()
            if missing:
                raise SystemExit(f"{path}: missing {sorted(missing)}")
            if not record["game"].get("platform") or not record["game"].get("storeId"):
                raise SystemExit(f"{path}: platform and storeId are required")
            if any(record["safety"].get(key) is not True for key in REQUIRED_SAFETY):
                raise SystemExit(f"{path}: profile must be offline singleplayer and multiplayer-blocked")
            if record["safety"].get("execution") != "user-guided-local-draft":
                raise SystemExit(f"{path}: executable trainer content is not permitted")
            if not record["features"]:
                raise SystemExit(f"{path}: at least one feature is required")

    print(f"Validated {profile_count} offline profiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
