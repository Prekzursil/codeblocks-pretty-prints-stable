from __future__ import annotations

import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.codeblocks_stable import (
    NoticeEntry,
    _case_insensitive_replace,
    _cmd_normalize_profile,
    _notice_category_from_name,
    _render_notice_inventory,
    build_managed_profile,
    collect_notice_inventory,
    load_json_document,
    main,
    normalize_profile_bundle,
    validate_payload_manifest,
    validate_release_inputs,
)


def _base_manifest() -> dict[str, object]:
    return {
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
        "profile_sources": [
            "default.conf",
            "default.cbKeyBinder20.conf",
            "codesnippets.ini",
        ],
        "profile_outputs": [
            "default.conf",
            "default.cbKeyBinder20.conf",
            "codesnippets.ini",
        ],
        "notice_name_patterns": [
            "LICENSE*",
            "gdbinit",
            "*.gdb.py",
        ],
        "profile_rewrites": {
            "debugger_executable": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\bin\gdb.exe",
            "debugger_python_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW\share\gcc-14.2.0\python",
            "toolchain_root": r"C:\Program Files\CodeBlocks Stable Toolchain Edition\MinGW",
            "profile_root": r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition",
        },
    }


class CodeblocksStableEdgeTests(unittest.TestCase):
    def test_load_json_document_rejects_non_object(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "bad.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_json_document(path)

    def test_case_insensitive_replace_replaces_case_insensitively(self) -> None:
        self.assertEqual(
            _case_insensitive_replace(r"C:\Program Files\CodeBlocks", r"c:\program files\codeblocks", r"C:\Stable"),
            r"C:\Stable",
        )

    def test_validate_payload_manifest_rejects_invalid_fields(self) -> None:
        invalid_cases = [
            ("schema_version", 2, "schema_version"),
            ("repo_name", "", "repo_name"),
            ("edition_name", "", "edition_name"),
            ("product_name", "", "product_name"),
            ("install_scope", "user", "install_scope"),
            ("host_architecture", "x86", "host_architecture"),
            ("target_architectures", ["x64"], "target_architectures"),
            ("bundled_toolchain", "wrong", "bundled_toolchain"),
            ("profile_sources", "wrong", "profile_sources"),
            ("profile_outputs", "wrong", "profile_outputs"),
            ("notice_name_patterns", "wrong", "notice_name_patterns"),
            ("profile_rewrites", "wrong", "profile_rewrites"),
        ]
        for key, replacement, expected in invalid_cases:
            with self.subTest(key=key):
                manifest = _base_manifest()
                manifest[key] = replacement
                with self.assertRaisesRegex(ValueError, expected):
                    validate_payload_manifest(manifest)

        for key in ("gcc_version", "gdb_version", "family"):
            with self.subTest(toolchain_key=key):
                manifest = _base_manifest()
                manifest["bundled_toolchain"][key] = ""
                with self.assertRaisesRegex(ValueError, key):
                    validate_payload_manifest(manifest)

        for key in (
            "debugger_executable",
            "debugger_python_root",
            "toolchain_root",
            "profile_root",
        ):
            with self.subTest(profile_key=key):
                manifest = _base_manifest()
                manifest["profile_rewrites"][key] = ""
                with self.assertRaisesRegex(ValueError, key):
                    validate_payload_manifest(manifest)

    def test_normalize_profile_bundle_rejects_missing_file(self) -> None:
        with self.assertRaisesRegex(ValueError, "profile bundle missing files"):
            normalize_profile_bundle(
                {
                    "default.conf": "x",
                    "default.cbKeyBinder20.conf": "{}",
                },
                _base_manifest(),
            )

    def test_build_managed_profile_reads_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "default.conf").write_text(r"C:\Program Files\CodeBlocks\MinGW", encoding="utf-8")
            (root / "default.cbKeyBinder20.conf").write_text("{}", encoding="utf-8")
            (root / "codesnippets.ini").write_text(
                r"SnippetFile=C:\Users\Prekzursil\AppData\Roaming\CodeBlocks\codesnippets.xml",
                encoding="utf-8",
            )
            bundle = build_managed_profile(root, _base_manifest())
            self.assertIn("CodeBlocks Stable Toolchain Edition", bundle["default.conf"])
            self.assertIn("CodeBlocks Stable Toolchain Edition", bundle["codesnippets.ini"])

    def test_notice_category_detection_prefers_custom_categories_then_defaults(self) -> None:
        categories = {"docs": ["README*"], "runtime": ["*gdb.py"]}
        self.assertEqual(
            _notice_category_from_name("README-notes.txt", categories, ["LICENSE*"]),
            "docs",
        )
        self.assertEqual(
            _notice_category_from_name("libstdc++.dll.a-gdb.py", categories, ["*.gdb.py"]),
            "runtime",
        )
        self.assertEqual(
            _notice_category_from_name("gdbinit", {}, ["gdbinit"]),
            "runtime_notice",
        )
        self.assertEqual(
            _notice_category_from_name("LICENSE.txt", {}, ["LICENSE*"]),
            "license",
        )
        self.assertIsNone(_notice_category_from_name("notes.txt", {}, ["LICENSE*"]))

    def test_collect_notice_inventory_handles_empty_and_invalid_category_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.assertEqual(collect_notice_inventory(root), [])

            manifest = {
                "included_patterns": ["LICENSE*"],
                "categories": "not-a-mapping",
            }
            with self.assertRaisesRegex(ValueError, "categories"):
                collect_notice_inventory(root, manifest)

    def test_render_notice_inventory_handles_empty_and_populated_inputs(self) -> None:
        self.assertIn("- None found", _render_notice_inventory([]))
        rendered = _render_notice_inventory([NoticeEntry(path="LICENSE.txt", category="license")])
        self.assertIn("LICENSE.txt", rendered)
        self.assertIn("license", rendered)

    def test_validate_release_inputs_rejects_bad_repo_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            (repo / "manifests").mkdir()
            (repo / "overlay").mkdir()

            (repo / "manifests" / "codeblocks_stable_toolchain.json").write_text(
                json.dumps(_base_manifest()),
                encoding="utf-8",
            )

            bad_notice = {
                "schema_version": 2,
                "included_patterns": ["LICENSE*"],
                "categories": {},
            }
            (repo / "manifests" / "notice_inventory.json").write_text(
                json.dumps(bad_notice),
                encoding="utf-8",
            )
            (repo / "overlay" / "profile_seed.json").write_text(
                json.dumps({"schema_version": 1, "seed_name": "seed", "debugger_init_commands": ["x"]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "notice_inventory schema_version"):
                validate_release_inputs(repo)

            bad_notice["schema_version"] = 1
            bad_notice["included_patterns"] = "wrong"
            (repo / "manifests" / "notice_inventory.json").write_text(
                json.dumps(bad_notice),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "included_patterns"):
                validate_release_inputs(repo)

            bad_notice["included_patterns"] = ["README*"]
            (repo / "manifests" / "notice_inventory.json").write_text(
                json.dumps(bad_notice),
                encoding="utf-8",
            )
            (repo / "overlay" / "profile_seed.json").write_text(
                json.dumps({"schema_version": 2, "seed_name": "seed", "debugger_init_commands": ["x"]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "overlay profile_seed schema_version"):
                validate_release_inputs(repo)

            (repo / "overlay" / "profile_seed.json").write_text(
                json.dumps({"schema_version": 1, "seed_name": "seed", "debugger_init_commands": []}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "debugger_init_commands"):
                validate_release_inputs(repo)

            (repo / "overlay" / "profile_seed.json").write_text(
                json.dumps({"schema_version": 1, "seed_name": "seed", "debugger_init_commands": ["x"]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "notice inventory is empty"):
                validate_release_inputs(repo)

    def test_command_handlers_and_main_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            profile = repo / "profile"
            profile.mkdir(parents=True)
            (profile / "default.conf").write_text(r"C:\Program Files\CodeBlocks\MinGW", encoding="utf-8")
            (profile / "default.cbKeyBinder20.conf").write_text("{}", encoding="utf-8")
            (profile / "codesnippets.ini").write_text(
                r"SnippetFile=C:\Users\Prekzursil\AppData\Roaming\CodeBlocks\codesnippets.xml",
                encoding="utf-8",
            )

            manifest_path = repo / "manifest.json"
            manifest_path.write_text(json.dumps(_base_manifest()), encoding="utf-8")

            out_dir = repo / "managed"
            rc = _cmd_normalize_profile(
                argparse.Namespace(
                    manifest=manifest_path,
                    source_profile=profile,
                    output_dir=out_dir,
                )
            )
            self.assertEqual(rc, 0)
            self.assertTrue((out_dir / "default.conf").exists())

            notice_root = repo / "payload"
            notice_root.mkdir()
            (notice_root / "LICENSE.txt").write_text("license", encoding="utf-8")
            notice_manifest_path = repo / "notice_manifest.json"
            notice_manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "included_patterns": ["LICENSE*"],
                        "categories": {"license": ["LICENSE*"]},
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = main(
                    [
                        "inventory-notices",
                        str(notice_root),
                        "--notice-manifest",
                        str(notice_manifest_path),
                        "--output",
                        "-",
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertIn("LICENSE.txt", stdout.getvalue())

            output_path = repo / "notice-output.json"
            rc = main(
                [
                    "inventory-notices",
                    str(notice_root),
                    "--notice-manifest",
                    str(notice_manifest_path),
                    "--output",
                    str(output_path),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertTrue(output_path.exists())

            rc = main(["validate-manifest", str(manifest_path)])
            self.assertEqual(rc, 0)

            notice_manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "included_patterns": ["LICENSE*"],
                        "categories": {"license": ["LICENSE*"]},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                main(
                    [
                        "inventory-notices",
                        str(notice_root),
                        "--notice-manifest",
                        str(notice_manifest_path),
                        "--output",
                        "-",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
