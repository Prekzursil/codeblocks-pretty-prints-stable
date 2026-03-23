from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.codeblocks_stable import load_manifest, validate_payload_manifest


class ManifestTests(unittest.TestCase):
    def test_manifest_loads_and_validates(self) -> None:
        manifest = load_manifest(Path(__file__).resolve().parents[1] / "manifests" / "codeblocks_stable_toolchain.json")
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["repo_name"], "codeblocks-pretty-prints-stable")
        self.assertEqual(manifest["edition_name"], "Code::Blocks Stable Toolchain Edition")
        self.assertIn("x86", manifest["target_architectures"])
        self.assertIn("x64", manifest["target_architectures"])
        self.assertIn("default.conf", manifest["profile_sources"])
        self.assertIn("gdbinit", manifest["notice_name_patterns"])
        validate_payload_manifest(manifest)

    def test_manifest_rejects_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "manifest.json"
            path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()

