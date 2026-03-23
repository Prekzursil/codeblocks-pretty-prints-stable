from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.quality import validate_release_inputs as validate_module


class ValidateReleaseInputsModuleTests(unittest.TestCase):
    def test_main_writes_summary_output(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tempdir:
            output_path = Path(tempdir) / "summary.json"
            rc = validate_module.main([str(repo_root), "--output", str(output_path)])
            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["manifest_name"], "codeblocks-pretty-prints-stable")
            self.assertEqual(payload["overlay_seed_name"], "codeblocks_stable_profile_seed")
            self.assertGreater(payload["notice_count"], 0)

    def test_main_without_output_path_still_succeeds(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        rc = validate_module.main([str(repo_root)])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()

