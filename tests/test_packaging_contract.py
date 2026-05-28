"""Tests for the packaging contract: profile seed and installer guard."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.codeblocks_stable import (
    main,
    materialize_profile_seed,
    validate_profile_overlay_contract,
    validate_release_inputs,
)
from tests.support import (
    base_manifest,
    write_profile_bundle,
    write_release_input_skeleton,
)

_CODESNIPPETS = (
    r"SnippetFile=C:\Users\Prekzursil\AppData\Roaming"
    r"\CodeBlocks\codesnippets.xml"
)
_EDITION = "CodeBlocks Stable Toolchain Edition"
_DELTREE_GUARD = (
    "if RemoveLegacyInstall and\n"
    "       CanSafelyRemoveLegacyInstall(DetectedLegacyInstallPath, "
    "ExpandConstant('{app}')) then\n"
    "    begin\n"
    "      DelTree(DetectedLegacyInstallPath, True, True, True);"
)


class PackagingContractTests(unittest.TestCase):
    """Validate profile-seed materialization and the installer script."""

    def test_materialize_profile_seed_writes_normalized_bundle(self) -> None:
        """Materializing a seed writes a normalized bundle and contract."""
        manifest = base_manifest()
        manifest["notice_name_patterns"] = ["LICENSE*", "gdbinit"]
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            source = root / "profile"
            write_profile_bundle(
                source,
                "\n".join(
                    [
                        r"C:\Program Files\CodeBlocks\MINGW\bin\gdb.exe",
                        r"C:\Program Files\CodeBlocks\MinGW"
                        r"\share\gcc-14.2.0\python",
                    ]
                ),
                _CODESNIPPETS,
            )
            output_dir = root / "overlay" / "profile-seed"
            replacements_path = root / "overlay" / "profile-replacements.json"

            written = materialize_profile_seed(
                source, manifest, output_dir, replacements_path
            )

            self.assertEqual(
                sorted(written.keys()), sorted(manifest["profile_outputs"])
            )
            self.assertTrue((output_dir / "default.conf").exists())
            self.assertIn(
                _EDITION,
                (output_dir / "default.conf").read_text(encoding="utf-8"),
            )
            replacements = json.loads(replacements_path.read_text(encoding="utf-8"))
            self.assertEqual(replacements["schema_version"], 1)
            self.assertIsInstance(replacements["replacements"], list)

    def test_validate_release_inputs_requires_seed_and_contract(self) -> None:
        """Validation fails when the materialized seed is missing."""
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            write_release_input_skeleton(repo)
            (repo / "overlay" / "profile_seed.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "seed_name": "seed",
                        "debugger_init_commands": ["x"],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "profile seed"):
                validate_release_inputs(repo)

    def test_materialize_profile_seed_command_and_overlay_validation(self) -> None:
        """The seed CLI command runs and overlay validation catches errors."""
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            source = root / "profile"
            write_profile_bundle(
                source,
                r"C:\Program Files\CodeBlocks\MinGW",
                _CODESNIPPETS,
            )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(base_manifest()), encoding="utf-8")

            output_dir = root / "overlay" / "profile-seed"
            replacements_path = root / "overlay" / "profile-replacements.json"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = main(
                    [
                        "materialize-profile-seed",
                        str(manifest_path),
                        str(source),
                        str(output_dir),
                        str(replacements_path),
                    ]
                )
            self.assertEqual(rc, 0)
            validate_profile_overlay_contract(
                json.loads(replacements_path.read_text(encoding="utf-8"))
            )

            with self.assertRaisesRegex(ValueError, "schema_version"):
                validate_profile_overlay_contract(
                    {"schema_version": 2, "replacements": []}
                )
            with self.assertRaisesRegex(ValueError, "must be a list"):
                validate_profile_overlay_contract(
                    {"schema_version": 1, "replacements": "bad"}
                )
            with self.assertRaisesRegex(ValueError, "must be an object"):
                validate_profile_overlay_contract(
                    {"schema_version": 1, "replacements": ["bad"]}
                )

    def test_installer_script_uses_safe_delete_guard(self) -> None:
        """The installer script guards legacy removal behind a safety check."""
        script = (
            Path(__file__).resolve().parents[1]
            / "packaging"
            / "CodeBlocksStableToolchainEdition.iss"
        ).read_text(encoding="utf-8")
        self.assertIn("AppId={{{#AppIdGuid}}}", script)
        self.assertIn(
            "OutputBaseFilename=codeblocks-pretty-prints-stable-"
            "{#AppVersion}-setup",
            script,
        )
        self.assertIn("function CanSafelyRemoveLegacyInstall", script)
        self.assertIn(
            "CanSafelyRemoveLegacyInstall(DetectedLegacyInstallPath, "
            "ExpandConstant('{app}'))",
            script,
        )
        self.assertIn(_DELTREE_GUARD, script)


if __name__ == "__main__":
    unittest.main()
