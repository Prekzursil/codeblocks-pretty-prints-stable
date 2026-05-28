"""Tests that each script ``__main__`` entrypoint runs end to end."""
from __future__ import annotations

import contextlib
import io
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support import (
    base_manifest,
    write_materialized_profile_seed,
    write_release_input_skeleton,
)

_NOTICE_MANIFEST = {
    "schema_version": 1,
    "included_patterns": ["printers.py"],
    "categories": {"runtime_notice": ["printers.py"]},
}
_GDB_INIT_PARTS = ("share", "CodeBlocks", "scripts", "gdb_init.gdb")
_PRINTERS_PARTS = (
    "MinGW", "share", "gcc-14.2.0", "python", "libstdcxx", "v6", "printers.py"
)


def _write_file(path: Path, content: str) -> None:
    """Create parent directories and write ``content`` to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ScriptEntrypointTests(unittest.TestCase):
    """Run each module's ``__main__`` guard via ``runpy``."""

    def test_codeblocks_stable_main_entrypoint(self) -> None:
        """The ``codeblocks_stable`` module runs as a script."""
        with tempfile.TemporaryDirectory() as tempdir:
            manifest_path = Path(tempdir) / "manifest.json"
            manifest_path.write_text(json.dumps(base_manifest()), encoding="utf-8")
            stdout = io.StringIO()
            argv = [
                "codeblocks_stable.py",
                "validate-manifest",
                str(manifest_path),
            ]
            with patch.object(sys, "argv", argv):
                with contextlib.redirect_stdout(stdout), self.assertRaises(
                    SystemExit
                ) as exc:
                    runpy.run_module(
                        "scripts.codeblocks_stable", run_name="__main__"
                    )
            self.assertEqual(exc.exception.code, 0)
            self.assertIn("validated manifest", stdout.getvalue())

    def test_codeblocks_release_main_entrypoint(self) -> None:
        """The ``codeblocks_release`` module runs as a script."""
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            repo = root / "repo"
            repo.mkdir()
            write_release_input_skeleton(repo, manifest=base_manifest())
            _write_file(
                repo / "manifests" / "notice_inventory.json",
                json.dumps(_NOTICE_MANIFEST),
            )
            write_materialized_profile_seed(repo)
            _write_file(repo / "THIRD_PARTY_NOTICES.md", "policy")

            source = root / "CodeBlocks"
            _write_file(source.joinpath(*_GDB_INIT_PARTS), "set print pretty on\n")
            _write_file(source / "codeblocks.exe", "binary")
            _write_file(source.joinpath(*_PRINTERS_PARTS), "printers")

            stdout = io.StringIO()
            argv = [
                "codeblocks_release.py",
                "prepare-local-release",
                "--repo-root",
                str(repo),
                "--source-install-root",
                str(source),
                "--version",
                "v0.1.0",
                "--output-root",
                str(repo / "dist"),
            ]
            with patch.object(sys, "argv", argv):
                with contextlib.redirect_stdout(stdout), self.assertRaises(
                    SystemExit
                ) as exc:
                    runpy.run_module(
                        "scripts.codeblocks_release", run_name="__main__"
                    )
            self.assertEqual(exc.exception.code, 0)
            self.assertIn("\"release_assets_root\"", stdout.getvalue())

    def test_normalize_coverage_xml_main_entrypoint(self) -> None:
        """The coverage-normalizer module runs as a script."""
        with tempfile.TemporaryDirectory() as tempdir:
            coverage_xml = Path(tempdir) / "coverage.xml"
            coverage_xml.write_text(
                '<coverage><packages><package name="scripts"><classes>'
                '<class name="codeblocks_stable.py" '
                'filename="codeblocks_stable.py" />'
                "</classes></package></packages></coverage>",
                encoding="utf-8",
            )
            argv = ["normalize_coverage_xml.py", str(coverage_xml)]
            with patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit) as exc:
                    runpy.run_module(
                        "scripts.quality.normalize_coverage_xml",
                        run_name="__main__",
                    )
            self.assertEqual(exc.exception.code, 0)

    def test_validate_release_inputs_main_entrypoint(self) -> None:
        """The release-input validator module runs as a script."""
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir) / "repo"
            repo.mkdir()
            write_release_input_skeleton(repo, manifest=base_manifest())
            write_materialized_profile_seed(repo)
            (repo / "overlay" / "profile_seed.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "seed_name": "seed",
                        "debugger_init_commands": ["set print pretty on"],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            argv = ["validate_release_inputs.py", str(repo)]
            with patch.object(sys, "argv", argv):
                with contextlib.redirect_stdout(stdout), self.assertRaises(
                    SystemExit
                ) as exc:
                    runpy.run_module(
                        "scripts.quality.validate_release_inputs",
                        run_name="__main__",
                    )
            self.assertEqual(exc.exception.code, 0)
            self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
