#!/usr/bin/env python3
"""Scan local launcher metadata and match installed games to SoloForge.

Supported scanners are intentionally local-file based:

- Steam library folders and app manifests
- GOG Galaxy install info files and best-effort Galaxy database rows
- Ubisoft Connect manifest/state files
- EA App installer metadata

The scanner does not sign in to launchers, query third-party services, inspect
memory, or modify files.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from scan_steam_libraries import (
    VdfError,
    default_steam_roots,
    library_paths_from_scan_roots,
    library_paths_from_steam_root,
    load_registry_games,
    normalize_title,
    parse_app_manifest,
    unique_paths,
)

ROOT = Path(__file__).resolve().parents[1]

LAUNCHER_PLATFORMS = {
    "steam": "steam",
    "gog": "gog",
    "ubisoft": "ubisoft-connect",
    "ea": "ea-app",
}

JSON_NAME_KEYS = ("name", "title", "gameName", "displayName", "productTitle")
JSON_ID_KEYS = ("gameId", "game_id", "productId", "product_id", "rootGameId", "appId", "app_id", "id")
JSON_PATH_KEYS = ("installPath", "install_path", "installationPath", "installation_path", "path", "installDir")


def default_roots(launcher: str) -> list[Path]:
    system = platform.system()
    home = Path.home()
    roots: list[Path] = []

    if launcher == "steam":
        return default_steam_roots()

    if launcher == "gog":
        if system == "Darwin":
            roots.extend(
                [
                    home / "Library" / "Application Support" / "GOG.com" / "Galaxy" / "storage",
                    home / "GOG Games",
                ]
            )
        elif system == "Windows":
            roots.extend(
                env_paths("ProgramData", "GOG.com/Galaxy/storage")
                + env_paths("ProgramFiles", "GOG Galaxy/Games")
                + env_paths("ProgramFiles(x86)", "GOG Galaxy/Games")
                + env_paths("USERPROFILE", "GOG Games")
            )
        else:
            roots.append(home / "GOG Games")

    if launcher == "ubisoft":
        if system == "Darwin":
            roots.append(home / "Library" / "Application Support" / "Ubisoft")
        elif system == "Windows":
            roots.extend(
                env_paths("ProgramFiles(x86)", "Ubisoft/Ubisoft Game Launcher")
                + env_paths("ProgramFiles", "Ubisoft/Ubisoft Game Launcher")
                + env_paths("ProgramData", "Ubisoft")
            )

    if launcher == "ea":
        if system == "Darwin":
            roots.append(home / "Library" / "Application Support" / "Electronic Arts")
        elif system == "Windows":
            roots.extend(
                env_paths("ProgramData", "EA Desktop")
                + env_paths("ProgramFiles", "EA Games")
                + env_paths("ProgramFiles", "Electronic Arts")
                + env_paths("ProgramFiles(x86)", "Electronic Arts")
            )

    return unique_paths([path for path in roots if path.exists()])


def env_paths(variable: str, suffix: str) -> list[Path]:
    value = os.environ.get(variable)
    return [Path(value) / Path(suffix)] if value else []


def as_list(values: Iterable[str] | None) -> list[Path]:
    return [Path(value).expanduser() for value in values or []]


def first_string(record: dict[str, Any], keys: Iterable[str]) -> str | None:
    for key in keys:
        value = record.get(key)
        if value is None:
            value = next((candidate for name, candidate in record.items() if name.lower() == key.lower()), None)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, int):
            return str(value)
    return None


def flatten_json(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(value, dict):
        records.append(value)
        for child in value.values():
            records.extend(flatten_json(child))
    elif isinstance(value, list):
        for child in value:
            records.extend(flatten_json(child))
    return records


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def match_registry_game(
    launcher: str,
    store_id: str | None,
    title: str,
    registry_games: list[dict[str, Any]],
) -> dict[str, Any] | None:
    platform = LAUNCHER_PLATFORMS[launcher]
    normalized_title = normalize_title(title)

    if store_id:
        for game in registry_games:
            known_id = game.get("game", {}).get("storeIds", {}).get(platform)
            if known_id == store_id:
                return game

    for game in registry_games:
        if normalize_title(game.get("game", {}).get("title", game.get("name", ""))) == normalized_title:
            return game

    return None


def build_game_record(
    launcher: str,
    name: str,
    store_id: str | None,
    library_path: Path | None,
    install_path: Path | None,
    registry_games: list[dict[str, Any]],
) -> dict[str, Any]:
    registry_match = match_registry_game(launcher, store_id, name, registry_games)
    record: dict[str, Any] = {
        "launcher": launcher,
        "platform": LAUNCHER_PLATFORMS[launcher],
        "name": name,
        "libraryPath": str(library_path) if library_path else None,
        "installPath": str(install_path) if install_path else None,
        "installed": install_path.exists() if install_path else None,
        "match": registry_match["id"] if registry_match else None,
        "safetyStatus": registry_match.get("safety", {}).get("reviewStatus") if registry_match else "requiresManualReview",
        "availableFeatures": [feature["name"] for feature in registry_match.get("features", [])] if registry_match else [],
    }
    if store_id:
        record["storeId"] = store_id
        if launcher == "steam":
            record["appid"] = store_id
    return record


def scan_steam(roots: list[Path], scan_roots: list[Path], registry_games: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    libraries: list[Path] = []
    for root in roots:
        libraries.extend(library_paths_from_steam_root(root.expanduser()))
    libraries.extend(library_paths_from_scan_roots(scan_roots))
    libraries = unique_paths(libraries)

    games: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for library in libraries:
        steamapps = library / "steamapps"
        for manifest in sorted(steamapps.glob("appmanifest_*.acf")):
            try:
                installed = parse_app_manifest(manifest)
            except VdfError as exc:
                errors.append({"launcher": "steam", "path": str(manifest), "error": str(exc)})
                continue

            install_path = steamapps / "common" / installed["installdir"]
            games.append(
                build_game_record(
                    "steam",
                    installed["name"],
                    installed["appid"],
                    library,
                    install_path,
                    registry_games,
                )
            )

    libraries_out = [{"launcher": "steam", "path": str(path)} for path in libraries]
    return games, libraries_out, errors


def scan_gog_info_file(path: Path, registry_games: list[dict[str, Any]]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None

    name = first_string(payload, JSON_NAME_KEYS)
    store_id = first_string(payload, JSON_ID_KEYS)
    if not name and not store_id:
        return None

    install_path = path.parent
    return build_game_record("gog", name or f"GOG game {store_id}", store_id, install_path.parent, install_path, registry_games)


def scan_gog_database(path: Path, registry_games: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    games: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    try:
        connection = sqlite3.connect(path)
    except sqlite3.Error as exc:
        return games, [{"launcher": "gog", "path": str(path), "error": str(exc)}]

    try:
        table_names = [
            row[0]
            for row in connection.execute("select name from sqlite_master where type='table'")
            if isinstance(row[0], str)
        ]
        for table in table_names:
            columns = [row[1] for row in connection.execute(f"pragma table_info({quote_identifier(table)})")]
            lower_columns = {column.lower(): column for column in columns}
            name_col = next((lower_columns.get(column.lower()) for column in JSON_NAME_KEYS if column.lower() in lower_columns), None)
            id_col = next((lower_columns.get(column.lower()) for column in JSON_ID_KEYS if column.lower() in lower_columns), None)
            path_col = next((lower_columns.get(column.lower()) for column in JSON_PATH_KEYS if column.lower() in lower_columns), None)
            if not (path_col and (name_col or id_col)):
                continue

            selected = [column for column in (name_col, id_col, path_col) if column]
            sql = f"select {', '.join(quote_identifier(column) for column in selected)} from {quote_identifier(table)}"
            for row in connection.execute(sql):
                values = dict(zip(selected, row))
                name = str(values.get(name_col) or values.get(id_col) or "GOG game")
                store_id = str(values[id_col]) if id_col and values.get(id_col) is not None else None
                install_path = Path(str(values[path_col])).expanduser() if values.get(path_col) else None
                games.append(build_game_record("gog", name, store_id, path.parent, install_path, registry_games))
    except sqlite3.Error as exc:
        errors.append({"launcher": "gog", "path": str(path), "error": str(exc)})
    finally:
        connection.close()

    return games, errors


def scan_gog(roots: list[Path], registry_games: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    games: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    seen_files: set[str] = set()

    for root in roots:
        if not root.exists():
            continue
        candidates = [root] if root.is_file() else list(root.glob("**/goggame-*.info")) + list(root.glob("**/galaxy-2.0.db"))
        for candidate in candidates:
            key = str(candidate)
            if key in seen_files:
                continue
            seen_files.add(key)
            if candidate.name.startswith("goggame-") and candidate.suffix == ".info":
                record = scan_gog_info_file(candidate, registry_games)
                if record:
                    games.append(record)
            elif candidate.name == "galaxy-2.0.db":
                db_games, db_errors = scan_gog_database(candidate, registry_games)
                games.extend(db_games)
                errors.extend(db_errors)

    libraries = [{"launcher": "gog", "path": str(path)} for path in roots if path.exists()]
    return games, libraries, errors


def parse_json_or_key_values(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if parsed is not None:
        candidates = flatten_json(parsed)
        return next((record for record in candidates if first_string(record, JSON_NAME_KEYS + JSON_ID_KEYS)), None)

    record: dict[str, Any] = {}
    for line in text.splitlines():
        match = re.match(r"\s*([A-Za-z0-9_.-]+)\s*[:=]\s*(.+?)\s*$", line)
        if match:
            record[match.group(1)] = match.group(2).strip().strip('"')
    return record or None


def scan_text_manifest(path: Path, launcher: str, registry_games: list[dict[str, Any]]) -> dict[str, Any] | None:
    try:
        payload = parse_json_or_key_values(path)
    except OSError:
        return None
    if not payload:
        return None

    name = first_string(payload, JSON_NAME_KEYS)
    store_id = first_string(payload, JSON_ID_KEYS)
    install_value = first_string(payload, JSON_PATH_KEYS)
    install_path = Path(install_value).expanduser() if install_value else path.parent
    if not name and not store_id:
        return None
    return build_game_record(launcher, name or f"{launcher} game {store_id}", store_id, path.parent, install_path, registry_games)


def scan_ubisoft(roots: list[Path], registry_games: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    games: list[dict[str, Any]] = []
    patterns = ("**/uplay_install.state", "**/*manifest*.json", "**/*install*.json", "**/*.yaml", "**/*.yml")
    for manifest in iter_existing_matches(roots, patterns):
        record = scan_text_manifest(manifest, "ubisoft", registry_games)
        if record:
            games.append(record)

    libraries = [{"launcher": "ubisoft", "path": str(path)} for path in roots if path.exists()]
    return dedupe_games(games), libraries, []


def scan_ea_xml(path: Path, registry_games: list[dict[str, Any]]) -> dict[str, Any] | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None

    values = {element.tag: (element.text or "").strip() for element in root.iter() if element.text}
    name = first_string(values, JSON_NAME_KEYS)
    store_id = first_string(values, JSON_ID_KEYS)
    install_value = first_string(values, JSON_PATH_KEYS)
    install_path = Path(install_value).expanduser() if install_value else path.parent.parent
    if not name and not store_id:
        return None
    return build_game_record("ea", name or f"EA game {store_id}", store_id, path.parent, install_path, registry_games)


def scan_ea(roots: list[Path], registry_games: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    games: list[dict[str, Any]] = []

    for manifest in iter_existing_matches(roots, ("**/__Installer/installerdata.xml", "**/*installerdata*.xml")):
        record = scan_ea_xml(manifest, registry_games)
        if record:
            games.append(record)

    for manifest in iter_existing_matches(roots, ("**/*install*.json", "**/*manifest*.json")):
        record = scan_text_manifest(manifest, "ea", registry_games)
        if record:
            games.append(record)

    libraries = [{"launcher": "ea", "path": str(path)} for path in roots if path.exists()]
    return dedupe_games(games), libraries, []


def iter_existing_matches(roots: list[Path], patterns: Iterable[str]) -> Iterable[Path]:
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            for match in root.glob(pattern):
                key = str(match)
                if match.is_file() and key not in seen:
                    seen.add(key)
                    yield match


def dedupe_games(games: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for game in games:
        key = (
            game.get("launcher") or "",
            game.get("storeId") or "",
            game.get("installPath") or game.get("name") or "",
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(game)
    return result


def scan_installed_games(
    launchers: list[str],
    roots: dict[str, list[Path]],
    scan_roots: list[Path],
) -> dict[str, Any]:
    registry_games = load_registry_games()
    games: list[dict[str, Any]] = []
    libraries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    if "steam" in launchers:
        launcher_games, launcher_libraries, launcher_errors = scan_steam(roots["steam"], scan_roots, registry_games)
        games.extend(launcher_games)
        libraries.extend(launcher_libraries)
        errors.extend(launcher_errors)

    if "gog" in launchers:
        launcher_games, launcher_libraries, launcher_errors = scan_gog(roots["gog"], registry_games)
        games.extend(launcher_games)
        libraries.extend(launcher_libraries)
        errors.extend(launcher_errors)

    if "ubisoft" in launchers:
        launcher_games, launcher_libraries, launcher_errors = scan_ubisoft(roots["ubisoft"], registry_games)
        games.extend(launcher_games)
        libraries.extend(launcher_libraries)
        errors.extend(launcher_errors)

    if "ea" in launchers:
        launcher_games, launcher_libraries, launcher_errors = scan_ea(roots["ea"], registry_games)
        games.extend(launcher_games)
        libraries.extend(launcher_libraries)
        errors.extend(launcher_errors)

    return {
        "generatedBy": "tools/scan_installed_games.py",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scanners": launchers,
        "libraries": libraries,
        "games": sorted(dedupe_games(games), key=lambda item: (item["launcher"], item["name"].lower())),
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan local launcher metadata for installed games.")
    parser.add_argument(
        "--launcher",
        action="append",
        choices=sorted(LAUNCHER_PLATFORMS),
        help="Launcher to scan. Can be passed more than once. Defaults to all launchers.",
    )
    parser.add_argument("--steam-root", action="append", default=[], help="Steam installation root.")
    parser.add_argument("--gog-root", action="append", default=[], help="GOG Galaxy storage folder, database, or game library root.")
    parser.add_argument("--ubisoft-root", action="append", default=[], help="Ubisoft Connect metadata or library root.")
    parser.add_argument("--ea-root", action="append", default=[], help="EA App metadata or library root.")
    parser.add_argument("--scan-root", action="append", default=[], help="Extra folder to search for Steam libraries.")
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    launchers = args.launcher or sorted(LAUNCHER_PLATFORMS)
    roots = {
        "steam": as_list(args.steam_root) or default_roots("steam"),
        "gog": as_list(args.gog_root) or default_roots("gog"),
        "ubisoft": as_list(args.ubisoft_root) or default_roots("ubisoft"),
        "ea": as_list(args.ea_root) or default_roots("ea"),
    }
    result = scan_installed_games(launchers, roots, as_list(args.scan_root))
    serialized = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
