#!/usr/bin/env python3
"""Validate SoloForge registry records without third-party dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "registry"
SCHEMA_VERSION = "0.1.0"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
IMPORT_MODES = {"metadata-only", "redistributable"}
REVIEW_STATUSES = {"approved", "requiresManualReview", "blocked"}
FEATURE_TYPES = {
    "config-patch",
    "save-tool",
    "mod-toggle",
    "memory-scan",
    "ct-reference",
    "guide",
    "map",
    "unknown",
}
BLOCKED_TEXT = {
    "anti-cheat bypass",
    "anticheat bypass",
    "multiplayer cheat",
    "online cheat",
    "drm bypass",
}


class ValidationError(Exception):
    """Raised when a registry file fails validation."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValidationError(f"{path}: top-level value must be an object")
    return data


def require_string(record: dict[str, Any], key: str, path: Path) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path}: `{key}` must be a non-empty string")
    return value


def validate_source(source: Any, path: Path) -> None:
    if not isinstance(source, dict):
        raise ValidationError(f"{path}: `source` must be an object")

    for key in ("name", "url", "importMode", "license", "lastChecked"):
        require_string(source, key, path)

    if source["importMode"] not in IMPORT_MODES:
        raise ValidationError(f"{path}: unsupported importMode `{source['importMode']}`")

    if source["license"].lower() in {"unknown", "mixed/unknown"} and source["importMode"] != "metadata-only":
        raise ValidationError(f"{path}: unknown license must use metadata-only import mode")


def validate_safety(safety: Any, path: Path) -> None:
    if not isinstance(safety, dict):
        raise ValidationError(f"{path}: `safety` must be an object")

    expected_true = ("singleplayerOnly", "offlineOnly", "multiplayerBlocked")
    for key in expected_true:
        if safety.get(key) is not True:
            raise ValidationError(f"{path}: safety.{key} must be true")

    status = safety.get("reviewStatus")
    if status not in REVIEW_STATUSES:
        raise ValidationError(f"{path}: invalid safety.reviewStatus `{status}`")


def validate_attribution(attribution: Any, path: Path) -> None:
    if not isinstance(attribution, dict):
        raise ValidationError(f"{path}: `attribution` must be an object")
    if not isinstance(attribution.get("required"), bool):
        raise ValidationError(f"{path}: attribution.required must be boolean")
    require_string(attribution, "text", path)


def validate_feature(feature: Any, path: Path) -> None:
    if not isinstance(feature, dict):
        raise ValidationError(f"{path}: feature must be an object")

    require_string(feature, "name", path)
    feature_type = require_string(feature, "type", path)
    if feature_type not in FEATURE_TYPES:
        raise ValidationError(f"{path}: invalid feature type `{feature_type}`")

    if feature.get("offlineOnly") is not True:
        raise ValidationError(f"{path}: every feature must be offlineOnly=true")

    if feature.get("safetyStatus") not in {"safe", "requiresManualReview", "blocked"}:
        raise ValidationError(f"{path}: invalid feature safetyStatus")


def validate_game(game: Any, path: Path) -> None:
    if not isinstance(game, dict):
        raise ValidationError(f"{path}: `game` must be an object")
    require_string(game, "title", path)
    platforms = game.get("platforms", [])
    if not isinstance(platforms, list) or not all(isinstance(item, str) for item in platforms):
        raise ValidationError(f"{path}: game.platforms must be a list of strings")


def validate_record(path: Path) -> None:
    record = load_json(path)

    if record.get("schemaVersion") != SCHEMA_VERSION:
        raise ValidationError(f"{path}: schemaVersion must be {SCHEMA_VERSION}")

    record_id = require_string(record, "id", path)
    if not ID_RE.match(record_id):
        raise ValidationError(f"{path}: invalid id `{record_id}`")

    if path.stem != record_id:
        raise ValidationError(f"{path}: filename must match id `{record_id}`")

    kind = require_string(record, "kind", path)
    if kind not in {"source", "game", "feature"}:
        raise ValidationError(f"{path}: invalid kind `{kind}`")

    require_string(record, "name", path)
    validate_source(record.get("source"), path)
    validate_safety(record.get("safety"), path)
    validate_attribution(record.get("attribution"), path)

    if kind == "game":
        validate_game(record.get("game"), path)
        features = record.get("features")
        if not isinstance(features, list) or not features:
            raise ValidationError(f"{path}: game records require at least one feature")
        for feature in features:
            validate_feature(feature, path)

    text = json.dumps(record, ensure_ascii=False).lower()
    for blocked in BLOCKED_TEXT:
        if blocked in text and record["safety"]["reviewStatus"] != "blocked":
            raise ValidationError(f"{path}: blocked phrase `{blocked}` requires blocked reviewStatus")


def registry_files() -> list[Path]:
    return sorted(REGISTRY_DIR.glob("sources/*.json")) + sorted(REGISTRY_DIR.glob("games/*.json"))


def main() -> int:
    files = registry_files()
    if not files:
        print("No registry files found", file=sys.stderr)
        return 1

    try:
        for path in files:
            validate_record(path)
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Validated {len(files)} registry files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
