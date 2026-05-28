"""Tests for payload-manifest loading and validation."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.codeblocks_stable import load_manifest, validate_payload_manifest


class ManifestTests(unittest.TestCase):
    """Validate the shipped manifest and rejection of bad manifests."""

    def test_manifest_loads_and_validates(self) -> None:
        """The shipped manifest loads and passes validation."""
        manifest_path = (
            Path(__file__).resolve().parents[1]
            / "manifests"
            / "codeblocks_stable_toolchain.json"
        )
        manifest = load_manifest(manifest_path)
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["repo_name"], "codeblocks-pretty-prints-stable")
        self.assertEqual(
            manifest["edition_name"], "Code::Blocks Stable Toolchain Edition"
        )
        self.assertIn("x86", manifest["target_architectures"])
        self.assertIn("x64", manifest["target_architectures"])
        self.assertIn("default.conf", manifest["profile_sources"])
        self.assertIn("gdbinit", manifest["notice_name_patterns"])
        validate_payload_manifest(manifest)

    def test_manifest_rejects_missing_fields(self) -> None:
        """A manifest missing required fields is rejected."""
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "manifest.json"
            path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()
