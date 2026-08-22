from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER_PATH = ROOT / "tools" / "scan_installed_games.py"

spec = importlib.util.spec_from_file_location("scan_installed_games", SCANNER_PATH)
scanner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(scanner)


class InstalledGameScannerTests(unittest.TestCase):
    def test_gog_info_file_matches_by_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game_dir = Path(temp) / "GOG Games" / "Cave Story+"
            game_dir.mkdir(parents=True)
            (game_dir / "goggame-200900.info").write_text(
                json.dumps({"name": "Cave Story+", "gameId": "200900"}),
                encoding="utf-8",
            )

            result = scanner.scan_installed_games(
                ["gog"],
                {
                    "steam": [],
                    "gog": [Path(temp)],
                    "ubisoft": [],
                    "ea": [],
                },
                [],
            )

        self.assertEqual(len(result["games"]), 1)
        self.assertEqual(result["games"][0]["launcher"], "gog")
        self.assertEqual(result["games"][0]["match"], "cave-story-plus")

    def test_gog_database_matches_by_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            db_path = Path(temp) / "galaxy-2.0.db"
            connection = sqlite3.connect(db_path)
            try:
                connection.execute(
                    "create table InstalledBaseProducts (productId text, title text, installationPath text)"
                )
                connection.execute(
                    "insert into InstalledBaseProducts values (?, ?, ?)",
                    ("1245620", "Elden Ring", str(Path(temp) / "ELDEN RING")),
                )
                connection.commit()
            finally:
                connection.close()

            result = scanner.scan_installed_games(
                ["gog"],
                {
                    "steam": [],
                    "gog": [db_path],
                    "ubisoft": [],
                    "ea": [],
                },
                [],
            )

        self.assertEqual(len(result["games"]), 1)
        self.assertEqual(result["games"][0]["match"], "elden-ring")

    def test_ubisoft_manifest_matches_by_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "data" / "5059" / "uplay_install.state"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps(
                    {
                        "gameId": "5059",
                        "name": "Assassin's Creed Odyssey",
                        "installPath": str(Path(temp) / "Assassins Creed Odyssey"),
                    }
                ),
                encoding="utf-8",
            )

            result = scanner.scan_installed_games(
                ["ubisoft"],
                {
                    "steam": [],
                    "gog": [],
                    "ubisoft": [Path(temp)],
                    "ea": [],
                },
                [],
            )

        self.assertEqual(len(result["games"]), 1)
        self.assertEqual(result["games"][0]["launcher"], "ubisoft")
        self.assertEqual(result["games"][0]["match"], "assassins-creed-odyssey")

    def test_ea_installer_xml_matches_by_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "Example Game" / "__Installer" / "installerdata.xml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                """
                <game>
                  <gameId>example</gameId>
                  <title>Example Game</title>
                  <installPath>/tmp/example-game</installPath>
                </game>
                """,
                encoding="utf-8",
            )

            result = scanner.scan_installed_games(
                ["ea"],
                {
                    "steam": [],
                    "gog": [],
                    "ubisoft": [],
                    "ea": [Path(temp)],
                },
                [],
            )

        self.assertEqual(len(result["games"]), 1)
        self.assertEqual(result["games"][0]["launcher"], "ea")
        self.assertEqual(result["games"][0]["match"], "example-game")


if __name__ == "__main__":
    unittest.main()
