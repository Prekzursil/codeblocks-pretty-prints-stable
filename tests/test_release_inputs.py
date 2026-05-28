"""Smoke test for release-input validation against the shipped repo."""
from __future__ import annotations

import unittest
from pathlib import Path

from scripts.codeblocks_stable import validate_release_inputs


class ReleaseInputValidationTests(unittest.TestCase):
    """Validate the repo's own release inputs end to end."""

    def test_validate_release_inputs_smoke(self) -> None:
        """Validation of the shipped repo succeeds and reports notices."""
        repo_root = Path(__file__).resolve().parents[1]
        result = validate_release_inputs(repo_root)
        self.assertGreater(result["notice_count"], 0)
        self.assertEqual(
            result["manifest"]["repo_name"], "codeblocks-pretty-prints-stable"
        )
        self.assertEqual(
            result["overlay_seed"]["seed_name"], "codeblocks_stable_profile_seed"
        )


if __name__ == "__main__":
    unittest.main()
