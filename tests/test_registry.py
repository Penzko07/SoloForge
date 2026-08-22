from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    def test_registry_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "validate_registry.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated", result.stdout)

    def test_app_data_contains_registry_snapshot(self) -> None:
        app_data = ROOT / "apps" / "desktop" / "app-data.js"
        self.assertTrue(app_data.exists())
        raw = app_data.read_text(encoding="utf-8")
        prefix = "window.SOLOFORGE_REGISTRY = "
        self.assertTrue(raw.startswith(prefix))
        payload = json.loads(raw[len(prefix) :].rstrip(";\n"))
        self.assertGreaterEqual(len(payload["sources"]), 2)
        self.assertGreaterEqual(len(payload["games"]), 1)

    def test_all_game_features_are_offline_only(self) -> None:
        for path in sorted((ROOT / "registry" / "games").glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            for feature in record.get("features", []):
                self.assertIs(feature.get("offlineOnly"), True, path.name)


if __name__ == "__main__":
    unittest.main()
