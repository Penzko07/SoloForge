from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ElectronScannerTests(unittest.TestCase):
    def test_scanner_cli_returns_expected_shape(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")

        result = subprocess.run(
            [node, str(ROOT / "apps" / "electron" / "scanner.cjs"), "--pretty"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["generatedBy"], "apps/electron/scanner.cjs")
        self.assertIn("steam", payload["scanners"])
        self.assertIsInstance(payload["games"], list)
        self.assertIsInstance(payload["libraries"], list)


if __name__ == "__main__":
    unittest.main()
