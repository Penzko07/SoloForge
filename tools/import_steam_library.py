#!/usr/bin/env python3
"""Build SoloForge cheat coverage from a Steam library source.

Inputs can be:

- a public Steam Community games XML page
- a saved SteamDB calculator HTML page
- a SoloForge installed-game scan JSON

The importer matches library games to existing SoloForge registry records. It
does not download trainer implementations and does not add multiplayer or
unreviewed games as executable cheats.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from scan_installed_games import load_registry_games, match_registry_game

APP_LINK_RE = re.compile(r"/app/(\d+)(?:/|$)")


class SteamDBAppParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.apps: list[dict[str, str]] = []
        self._current_appid: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = dict(attrs)
        href = attributes.get("href") or ""
        match = APP_LINK_RE.search(href)
        if match:
            self._current_appid = match.group(1)
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._current_appid:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._current_appid:
            return
        name = " ".join("".join(self._text).split())
        if name and not any(app["appid"] == self._current_appid for app in self.apps):
            self.apps.append({"appid": self._current_appid, "name": name})
        self._current_appid = None
        self._text = []


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SoloForge/0.1 (+https://github.com/Penzko07/SoloForge)",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def steam_community_games_url(steam_id: str) -> str:
    return f"https://steamcommunity.com/profiles/{steam_id}/games?tab=all&xml=1"


def parse_steam_community_xml(text: str) -> list[dict[str, str]]:
    root = ET.fromstring(text)
    games = []
    for game in root.findall(".//game"):
        appid = (game.findtext("appID") or "").strip()
        name = (game.findtext("name") or "").strip()
        if appid and name:
            games.append({"appid": appid, "name": name})
    return dedupe_library_games(games)


def parse_steamdb_html(text: str) -> list[dict[str, str]]:
    parser = SteamDBAppParser()
    parser.feed(text)
    return dedupe_library_games(parser.apps)


def parse_scan_json(text: str) -> list[dict[str, str]]:
    payload = json.loads(text)
    games = []
    for game in payload.get("games", []):
        if game.get("launcher") not in (None, "steam"):
            continue
        appid = str(game.get("appid") or game.get("storeId") or "").strip()
        name = str(game.get("name") or "").strip()
        if appid and name:
            games.append({"appid": appid, "name": name})
    return dedupe_library_games(games)


def dedupe_library_games(games: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result = []
    for game in games:
        appid = game["appid"]
        if appid in seen:
            continue
        seen.add(appid)
        result.append(game)
    return sorted(result, key=lambda item: item["name"].lower())


def feature_names(record: dict[str, Any] | None) -> list[str]:
    if not record:
        return []
    return [feature["name"] for feature in record.get("features", []) if feature.get("offlineOnly") is True]


def build_coverage_report(library_games: list[dict[str, str]], steam_id: str | None, source: str) -> dict[str, Any]:
    registry_games = load_registry_games()
    games = []

    for library_game in library_games:
        registry_match = match_registry_game("steam", library_game["appid"], library_game["name"], registry_games)
        safety = registry_match.get("safety", {}) if registry_match else {}
        eligible = bool(
            registry_match
            and safety.get("singleplayerOnly") is True
            and safety.get("offlineOnly") is True
            and safety.get("multiplayerBlocked") is True
            and safety.get("reviewStatus") != "blocked"
        )
        games.append(
            {
                "appid": library_game["appid"],
                "name": library_game["name"],
                "match": registry_match["id"] if registry_match else None,
                "singleplayerEligible": eligible,
                "availableFeatures": feature_names(registry_match) if eligible else [],
                "achievementCompatibility": "neutral-by-policy" if eligible else "unknown",
                "notes": "Matched metadata only; executable trainer content requires license and safety review."
                if eligible
                else "No approved SoloForge singleplayer metadata match yet.",
            }
        )

    matched = [game for game in games if game["match"]]
    eligible = [game for game in games if game["singleplayerEligible"]]
    return {
        "generatedBy": "tools/import_steam_library.py",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "steamId": steam_id,
        "summary": {
            "libraryGames": len(games),
            "registryMatches": len(matched),
            "singleplayerEligible": len(eligible),
            "withTools": len([game for game in eligible if game["availableFeatures"]]),
        },
        "games": games,
    }


def read_input_games(args: argparse.Namespace) -> tuple[list[dict[str, str]], str]:
    if args.steam_id:
        url = steam_community_games_url(args.steam_id)
        return parse_steam_community_xml(fetch_text(url)), url
    if args.steamdb_html:
        path = Path(args.steamdb_html)
        return parse_steamdb_html(path.read_text(encoding="utf-8", errors="replace")), str(path)
    if args.scan_json:
        path = Path(args.scan_json)
        return parse_scan_json(path.read_text(encoding="utf-8", errors="replace")), str(path)
    raise ValueError("provide --steam-id, --steamdb-html, or --scan-json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Match a Steam library to SoloForge singleplayer cheat metadata.")
    parser.add_argument("--steam-id", help="SteamID64 for a public Steam Community games XML lookup.")
    parser.add_argument("--steamdb-html", help="Saved SteamDB calculator HTML file.")
    parser.add_argument("--scan-json", help="SoloForge installed-game scan JSON.")
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    try:
        library_games, source = read_input_games(args)
    except (OSError, ValueError, ET.ParseError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(f"Steam library import failed: {exc}", file=sys.stderr)
        return 1

    report = build_coverage_report(library_games, args.steam_id, source)
    serialized = json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
