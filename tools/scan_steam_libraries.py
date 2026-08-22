#!/usr/bin/env python3
"""Scan local Steam libraries and match installed games to SoloForge registry.

This tool reads local Steam metadata only:

- steamapps/libraryfolders.vdf
- steamapps/appmanifest_*.acf

It does not query SteamDB, does not require Steam credentials, and does not
attach to game processes.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / "registry"


class VdfError(Exception):
    """Raised when a VDF file cannot be parsed."""


TOKEN_RE = re.compile(r'"((?:\\.|[^"\\])*)"|([{}])')


def decode_vdf_string(value: str) -> str:
    return value.replace(r"\\", "\\").replace(r"\"", '"')


def tokenize_vdf(text: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_RE.finditer(text):
        if match.group(2):
            tokens.append(match.group(2))
        else:
            tokens.append(decode_vdf_string(match.group(1)))
    return tokens


def parse_vdf(text: str) -> dict[str, Any]:
    tokens = tokenize_vdf(text)
    index = 0

    def parse_object() -> dict[str, Any]:
        nonlocal index
        result: dict[str, Any] = {}
        while index < len(tokens):
            token = tokens[index]
            if token == "}":
                index += 1
                break
            if token == "{":
                raise VdfError("unexpected `{`")

            key = token
            index += 1
            if index >= len(tokens):
                raise VdfError(f"missing value for `{key}`")

            value = tokens[index]
            index += 1
            if value == "{":
                result[key] = parse_object()
            elif value == "}":
                raise VdfError(f"unexpected end after `{key}`")
            else:
                result[key] = value
        return result

    parsed = parse_object()
    if index != len(tokens):
        raise VdfError("trailing tokens")
    return parsed


def read_vdf(path: Path) -> dict[str, Any]:
    return parse_vdf(path.read_text(encoding="utf-8", errors="replace"))


def default_steam_roots() -> list[Path]:
    system = platform.system()
    home = Path.home()
    roots: list[Path] = []

    if system == "Darwin":
        roots.append(home / "Library" / "Application Support" / "Steam")
    elif system == "Windows":
        candidates = [
            os.environ.get("ProgramFiles(x86)"),
            os.environ.get("ProgramFiles"),
        ]
        roots.extend(Path(path) / "Steam" for path in candidates if path)
    else:
        roots.extend(
            [
                home / ".steam" / "steam",
                home / ".local" / "share" / "Steam",
                home / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",
            ]
        )

    return unique_paths([path for path in roots if path.exists()])


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        normalized = str(path.expanduser())
        if normalized not in seen:
            seen.add(normalized)
            result.append(path.expanduser())
    return result


def library_paths_from_steam_root(steam_root: Path) -> list[Path]:
    steamapps = steam_root / "steamapps"
    library_file = steamapps / "libraryfolders.vdf"
    libraries = [steam_root]

    if not library_file.exists():
        return unique_paths([path for path in libraries if (path / "steamapps").exists()])

    data = read_vdf(library_file)
    root = data.get("libraryfolders", data)
    if not isinstance(root, dict):
        return unique_paths(libraries)

    for value in root.values():
        if isinstance(value, dict) and isinstance(value.get("path"), str):
            libraries.append(Path(value["path"]))

    return unique_paths([path for path in libraries if (path / "steamapps").exists()])


def library_paths_from_scan_roots(scan_roots: list[Path]) -> list[Path]:
    libraries: list[Path] = []
    for scan_root in scan_roots:
        root = scan_root.expanduser()
        if (root / "steamapps").exists():
            libraries.append(root)
        for steamapps in root.glob("**/steamapps"):
            libraries.append(steamapps.parent)
    return unique_paths(libraries)


def parse_app_manifest(path: Path) -> dict[str, str]:
    data = read_vdf(path)
    app_state = data.get("AppState", data)
    if not isinstance(app_state, dict):
        raise VdfError("app manifest missing AppState")

    appid = app_state.get("appid")
    name = app_state.get("name")
    installdir = app_state.get("installdir")
    if not isinstance(appid, str) or not isinstance(name, str) or not isinstance(installdir, str):
        raise VdfError("app manifest missing appid, name, or installdir")

    return {
        "appid": appid,
        "name": name,
        "installdir": installdir,
    }


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def load_registry_games() -> list[dict[str, Any]]:
    games = []
    for path in sorted((REGISTRY_DIR / "games").glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            games.append(json.load(handle))
    return games


def match_registry_game(installed: dict[str, str], registry_games: list[dict[str, Any]]) -> dict[str, Any] | None:
    appid = installed["appid"]
    normalized_name = normalize_title(installed["name"])

    for game in registry_games:
        steam_id = game.get("game", {}).get("storeIds", {}).get("steam")
        if steam_id == appid:
            return game

    for game in registry_games:
        if normalize_title(game.get("game", {}).get("title", game.get("name", ""))) == normalized_name:
            return game

    return None


def scan_libraries(steam_roots: list[Path], scan_roots: list[Path]) -> dict[str, Any]:
    libraries: list[Path] = []
    for root in steam_roots:
        libraries.extend(library_paths_from_steam_root(root.expanduser()))
    libraries.extend(library_paths_from_scan_roots(scan_roots))
    libraries = unique_paths(libraries)

    registry_games = load_registry_games()
    games = []
    errors = []

    for library in libraries:
        steamapps = library / "steamapps"
        for manifest in sorted(steamapps.glob("appmanifest_*.acf")):
            try:
                installed = parse_app_manifest(manifest)
            except VdfError as exc:
                errors.append({"path": str(manifest), "error": str(exc)})
                continue

            install_path = steamapps / "common" / installed["installdir"]
            registry_match = match_registry_game(installed, registry_games)
            games.append(
                {
                    "appid": installed["appid"],
                    "name": installed["name"],
                    "libraryPath": str(library),
                    "installPath": str(install_path),
                    "installed": install_path.exists(),
                    "match": registry_match["id"] if registry_match else None,
                    "safetyStatus": registry_match.get("safety", {}).get("reviewStatus") if registry_match else "requiresManualReview",
                    "availableFeatures": [feature["name"] for feature in registry_match.get("features", [])] if registry_match else [],
                }
            )

    return {
        "generatedBy": "tools/scan_steam_libraries.py",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "libraries": [str(path) for path in libraries],
        "games": sorted(games, key=lambda item: item["name"].lower()),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan local Steam libraries for installed games.")
    parser.add_argument(
        "--steam-root",
        action="append",
        default=[],
        help="Steam installation root. Can be passed more than once.",
    )
    parser.add_argument(
        "--scan-root",
        action="append",
        default=[],
        help="Directory to search recursively for steamapps folders. Can be passed more than once.",
    )
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    steam_roots = [Path(path) for path in args.steam_root] or default_steam_roots()
    scan_roots = [Path(path) for path in args.scan_root]
    result = scan_libraries(steam_roots, scan_roots)
    serialized = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
