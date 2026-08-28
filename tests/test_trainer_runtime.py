from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TrainerRuntimeTests(unittest.TestCase):
    def test_runtime_status_cli_returns_expected_shape(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not available")

        result = subprocess.run(
            [node, str(ROOT / "apps" / "electron" / "trainer-runtime.cjs"), "--pretty"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("platform", payload)
        self.assertIn("available", payload)
        self.assertIn(payload["mode"], {"native-memory", "preview"})


if __name__ == "__main__":
    unittest.main()
