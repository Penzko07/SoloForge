#!/usr/bin/env python3
"""Generate the static app registry snapshot."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "registry"
APP_DATA = ROOT / "apps" / "desktop" / "app-data.js"


def load_records(pattern: str) -> list[dict]:
    records = []
    for path in sorted(REGISTRY_DIR.glob(pattern)):
        with path.open("r", encoding="utf-8") as handle:
            records.append(json.load(handle))
    return records


def main() -> int:
    payload = {
        "generatedBy": "tools/update_app_data.py",
        "schemaVersion": "0.1.0",
        "sources": load_records("sources/*.json"),
        "games": load_records("games/*.json"),
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    APP_DATA.write_text(
        "window.SOLOFORGE_REGISTRY = "
        + serialized
        + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {APP_DATA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
