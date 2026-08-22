from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER_PATH = ROOT / "tools" / "scan_steam_libraries.py"

spec = importlib.util.spec_from_file_location("scan_steam_libraries", SCANNER_PATH)
scanner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(scanner)


class SteamScannerTests(unittest.TestCase):
    def test_parse_vdf_nested_object(self) -> None:
        parsed = scanner.parse_vdf(
            '''
            "libraryfolders"
            {
              "0"
              {
                "path" "/Games/Steam"
                "apps"
                {
                  "1245620" "123456"
                }
              }
            }
            '''
        )

        self.assertEqual(parsed["libraryfolders"]["0"]["path"], "/Games/Steam")
        self.assertEqual(parsed["libraryfolders"]["0"]["apps"]["1245620"], "123456")

    def test_scan_libraries_matches_registry_by_appid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            steam_root = base / "Steam"
            extra_library = base / "Games" / "SteamLibrary"
            (steam_root / "steamapps").mkdir(parents=True)
            (extra_library / "steamapps" / "common" / "ELDEN RING").mkdir(parents=True)

            (steam_root / "steamapps" / "libraryfolders.vdf").write_text(
                f'''
                "libraryfolders"
                {{
                  "0" {{ "path" "{steam_root}" }}
                  "1" {{ "path" "{extra_library}" }}
                }}
                ''',
                encoding="utf-8",
            )

            (extra_library / "steamapps" / "appmanifest_1245620.acf").write_text(
                '''
                "AppState"
                {
                  "appid" "1245620"
                  "name" "ELDEN RING"
                  "installdir" "ELDEN RING"
                }
                ''',
                encoding="utf-8",
            )

            result = scanner.scan_libraries([steam_root], [])

        self.assertEqual(len(result["libraries"]), 2)
        self.assertEqual(len(result["games"]), 1)
        self.assertEqual(result["games"][0]["match"], "elden-ring")
        self.assertIn("Cheat table reference", result["games"][0]["availableFeatures"])
        self.assertIn("Rune value finder", result["games"][0]["availableFeatures"])


if __name__ == "__main__":
    unittest.main()
