from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.codeblocks_stable import main, materialize_profile_seed, validate_profile_overlay_contract, validate_release_inputs


class PackagingContractTests(unittest.TestCase):
    def test_materialize_profile_seed_writes_normalized_bundle_and_overlay_map(self) -> None:
        manifest = {
            "schema_version": 1,
            "repo_name": "codeblocks-pretty-prints-stable",
            "edition_name": "Code::Blocks Stable Toolchain Edition",
            "product_name": "Code::Blocks",
            "install_scope": "machine-wide",
            "host_architecture": "x64",
            "target_architectures": ["x86", "x64"],
            "current_official_install_root": r"C:\Program Files\CodeBlocks",
            "edition_install_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition",
            "current_profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks",
            "managed_profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition",
            "toolchain_relative_root": "MinGW",
            "toolchain_python_relative_root": r"share\gcc-14.2.0\python",
            "bundled_toolchain": {
                "gcc_version": "14.2.0",
                "gdb_version": "16.2",
                "family": "mingw-w64-ucrt-posix-seh",
            },
            "profile_sources": ["default.conf", "default.cbKeyBinder20.conf", "codesnippets.ini"],
            "profile_outputs": ["default.conf", "default.cbKeyBinder20.conf", "codesnippets.ini"],
            "notice_name_patterns": ["LICENSE*", "gdbinit"],
            "profile_rewrites": {
                "debugger_executable": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\bin\gdb.exe",
                "debugger_python_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\share\gcc-14.2.0\python",
                "toolchain_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW",
                "profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition",
            },
        }
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            source = root / "profile"
            source.mkdir()
            (source / "default.conf").write_text(
                "\n".join(
                    [
                        r"C:\Program Files\CodeBlocks\MINGW\bin\gdb.exe",
                        r"C:\Program Files\CodeBlocks\MinGW\share\gcc-14.2.0\python",
                    ]
                ),
                encoding="utf-8",
            )
            (source / "default.cbKeyBinder20.conf").write_text("{}", encoding="utf-8")
            (source / "codesnippets.ini").write_text(
                r"SnippetFile=C:\Users\Prekzursil\AppData\Roaming\CodeBlocks\codesnippets.xml",
                encoding="utf-8",
            )
            output_dir = root / "overlay" / "profile-seed"
            replacements_path = root / "overlay" / "profile-replacements.json"

            written = materialize_profile_seed(source, manifest, output_dir, replacements_path)

            self.assertEqual(sorted(written.keys()), sorted(manifest["profile_outputs"]))
            self.assertTrue((output_dir / "default.conf").exists())
            self.assertIn("CodeBlocks Stable Toolchain Edition", (output_dir / "default.conf").read_text(encoding="utf-8"))
            replacements = json.loads(replacements_path.read_text(encoding="utf-8"))
            self.assertEqual(replacements["schema_version"], 1)
            self.assertIsInstance(replacements["replacements"], list)

    def test_validate_release_inputs_requires_materialized_profile_seed_and_overlay_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            (repo / "manifests").mkdir()
            (repo / "overlay").mkdir()
            (repo / "LICENSE.txt").write_text("license", encoding="utf-8")
            manifest = {
                "schema_version": 1,
                "repo_name": "codeblocks-pretty-prints-stable",
                "edition_name": "Code::Blocks Stable Toolchain Edition",
                "product_name": "Code::Blocks",
                "install_scope": "machine-wide",
                "host_architecture": "x64",
                "target_architectures": ["x86", "x64"],
                "current_official_install_root": r"C:\Program Files\CodeBlocks",
                "edition_install_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition",
                "current_profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks",
                "managed_profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition",
                "toolchain_relative_root": "MinGW",
                "toolchain_python_relative_root": r"share\gcc-14.2.0\python",
                "bundled_toolchain": {"gcc_version": "14.2.0", "gdb_version": "16.2", "family": "mingw-w64-ucrt-posix-seh"},
                "profile_sources": ["default.conf", "default.cbKeyBinder20.conf", "codesnippets.ini"],
                "profile_outputs": ["default.conf", "default.cbKeyBinder20.conf", "codesnippets.ini"],
                "notice_name_patterns": ["LICENSE*"],
                "profile_rewrites": {
                    "debugger_executable": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\bin\gdb.exe",
                    "debugger_python_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\share\gcc-14.2.0\python",
                    "toolchain_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW",
                    "profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition",
                },
            }
            (repo / "manifests" / "codeblocks_stable_toolchain.json").write_text(json.dumps(manifest), encoding="utf-8")
            (repo / "manifests" / "notice_inventory.json").write_text(
                json.dumps({"schema_version": 1, "included_patterns": ["LICENSE*"], "categories": {"license": ["LICENSE*"]}}),
                encoding="utf-8",
            )
            (repo / "overlay" / "profile_seed.json").write_text(
                json.dumps({"schema_version": 1, "seed_name": "seed", "debugger_init_commands": ["x"]}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "profile seed"):
                validate_release_inputs(repo)

    def test_materialize_profile_seed_command_and_overlay_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            source = root / "profile"
            source.mkdir()
            (source / "default.conf").write_text(r"C:\Program Files\CodeBlocks\MinGW", encoding="utf-8")
            (source / "default.cbKeyBinder20.conf").write_text("{}", encoding="utf-8")
            (source / "codesnippets.ini").write_text(
                r"SnippetFile=C:\Users\Prekzursil\AppData\Roaming\CodeBlocks\codesnippets.xml",
                encoding="utf-8",
            )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "repo_name": "codeblocks-pretty-prints-stable",
                        "edition_name": "Code::Blocks Stable Toolchain Edition",
                        "product_name": "Code::Blocks",
                        "install_scope": "machine-wide",
                        "host_architecture": "x64",
                        "target_architectures": ["x86", "x64"],
                        "current_official_install_root": r"C:\Program Files\CodeBlocks",
                        "edition_install_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition",
                        "current_profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks",
                        "managed_profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition",
                        "toolchain_relative_root": "MinGW",
                        "toolchain_python_relative_root": r"share\gcc-14.2.0\python",
                        "bundled_toolchain": {"gcc_version": "14.2.0", "gdb_version": "16.2", "family": "mingw-w64-ucrt-posix-seh"},
                        "profile_sources": ["default.conf", "default.cbKeyBinder20.conf", "codesnippets.ini"],
                        "profile_outputs": ["default.conf", "default.cbKeyBinder20.conf", "codesnippets.ini"],
                        "notice_name_patterns": ["LICENSE*"],
                        "profile_rewrites": {
                            "debugger_executable": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\bin\gdb.exe",
                            "debugger_python_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\share\gcc-14.2.0\python",
                            "toolchain_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW",
                            "profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition",
                        },
                    }
                ),
                encoding="utf-8",
            )

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
            validate_profile_overlay_contract(json.loads(replacements_path.read_text(encoding="utf-8")))

            with self.assertRaisesRegex(ValueError, "schema_version"):
                validate_profile_overlay_contract({"schema_version": 2, "replacements": []})
            with self.assertRaisesRegex(ValueError, "must be a list"):
                validate_profile_overlay_contract({"schema_version": 1, "replacements": "bad"})
            with self.assertRaisesRegex(ValueError, "must be an object"):
                validate_profile_overlay_contract({"schema_version": 1, "replacements": ["bad"]})

    def test_installer_script_uses_safe_delete_guard(self) -> None:
        script = (Path(__file__).resolve().parents[1] / "packaging" / "CodeBlocksStableToolchainEdition.iss").read_text(encoding="utf-8")
        self.assertIn("function CanSafelyRemoveLegacyInstall", script)
        self.assertIn("CanSafelyRemoveLegacyInstall(DetectedLegacyInstallPath, ExpandConstant('{app}'))", script)
        self.assertIn(
            "if RemoveLegacyInstall and\n       CanSafelyRemoveLegacyInstall(DetectedLegacyInstallPath, ExpandConstant('{app}')) then\n    begin\n      DelTree(DetectedLegacyInstallPath, True, True, True);",
            script,
        )


if __name__ == "__main__":
    unittest.main()
