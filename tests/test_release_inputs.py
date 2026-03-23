from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.codeblocks_stable import validate_release_inputs


class ReleaseInputValidationTests(unittest.TestCase):
    def test_validate_release_inputs_smoke(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        result = validate_release_inputs(repo_root)
        self.assertGreater(result["notice_count"], 0)
        self.assertEqual(result["manifest"]["repo_name"], "codeblocks-pretty-prints-stable")
        self.assertEqual(result["overlay_seed"]["seed_name"], "codeblocks_stable_profile_seed")


if __name__ == "__main__":
    unittest.main()

