from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPORTER_PATH = ROOT / "tools" / "import_steam_library.py"

spec = importlib.util.spec_from_file_location("import_steam_library", IMPORTER_PATH)
importer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(importer)


class SteamLibraryImporterTests(unittest.TestCase):
    def test_parse_steam_community_xml(self) -> None:
        games = importer.parse_steam_community_xml(
            """
            <gamesList>
              <games>
                <game><appID>1245620</appID><name>ELDEN RING</name></game>
                <game><appID>374320</appID><name>Dark Souls III</name></game>
              </games>
            </gamesList>
            """
        )

        self.assertEqual([game["appid"] for game in games], ["374320", "1245620"])

    def test_parse_steamdb_html(self) -> None:
        games = importer.parse_steamdb_html(
            """
            <table>
              <tr><td><a href="/app/812140/">Assassin's Creed Odyssey</a></td></tr>
              <tr><td><a href="/app/812140/">Assassin's Creed Odyssey</a></td></tr>
              <tr><td><a href="/app/270050/">Quest of Dungeons</a></td></tr>
            </table>
            """
        )

        self.assertEqual([game["appid"] for game in games], ["812140", "270050"])

    def test_build_coverage_report_matches_registry(self) -> None:
        report = importer.build_coverage_report(
            [{"appid": "1245620", "name": "ELDEN RING"}, {"appid": "999", "name": "Unknown"}],
            "76561198108903649",
            "test",
        )

        self.assertEqual(report["summary"]["libraryGames"], 2)
        self.assertEqual(report["summary"]["registryMatches"], 1)
        self.assertEqual(report["summary"]["singleplayerEligible"], 1)
        self.assertEqual(report["games"][0]["achievementCompatibility"], "neutral-by-policy")


if __name__ == "__main__":
    unittest.main()
