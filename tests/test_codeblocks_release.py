from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.codeblocks_release import (
    DEV_ONLY_GDB_SOURCE,
    PATCHED_GDB_COMMENT,
    build_provenance,
    build_release_manifest,
    build_sbom,
    compose_notice_policy,
    main,
    patch_staged_gdb_init,
    prepare_local_release,
    render_release_notes,
    sanitize_gdb_init,
)
from tests.support import base_manifest, write_materialized_profile_seed, write_release_input_skeleton


class CodeblocksReleaseTests(unittest.TestCase):
    def test_sanitize_gdb_init_replaces_dev_only_source(self) -> None:
        original = "\n".join(
            [
                "set print pretty on",
                DEV_ONLY_GDB_SOURCE,
                "set args --debug-log",
            ]
        )
        patched = sanitize_gdb_init(original)
        self.assertNotIn(DEV_ONLY_GDB_SOURCE, patched)
        self.assertIn(PATCHED_GDB_COMMENT, patched)
        self.assertTrue(patched.endswith("\n"))

    def test_patch_staged_gdb_init_updates_staged_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            payload_root = Path(tempdir)
            gdb_init = payload_root / "share" / "CodeBlocks" / "scripts" / "gdb_init.gdb"
            gdb_init.parent.mkdir(parents=True, exist_ok=True)
            gdb_init.write_text(DEV_ONLY_GDB_SOURCE + "\n", encoding="utf-8")
            self.assertTrue(patch_staged_gdb_init(payload_root))
            self.assertIn(PATCHED_GDB_COMMENT, gdb_init.read_text(encoding="utf-8"))

    def test_patch_staged_gdb_init_handles_missing_or_already_clean_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            payload_root = Path(tempdir)
            self.assertFalse(patch_staged_gdb_init(payload_root))
            gdb_init = payload_root / "share" / "CodeBlocks" / "scripts" / "gdb_init.gdb"
            gdb_init.parent.mkdir(parents=True, exist_ok=True)
            gdb_init.write_text("set print pretty on\n", encoding="utf-8")
            self.assertFalse(patch_staged_gdb_init(payload_root))
            self.assertEqual(gdb_init.read_text(encoding="utf-8"), "set print pretty on\n")

    def test_prepare_local_release_stages_payload_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            repo = root / "repo"
            repo.mkdir()
            write_release_input_skeleton(repo, manifest=base_manifest())
            (repo / "manifests" / "notice_inventory.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "included_patterns": ["printers.py"],
                        "categories": {"runtime_notice": ["printers.py"]},
                    }
                ),
                encoding="utf-8",
            )
            write_materialized_profile_seed(repo)
            (repo / "THIRD_PARTY_NOTICES.md").write_text("policy", encoding="utf-8")

            source_install_root = root / "CodeBlocks"
            (source_install_root / "share" / "CodeBlocks" / "scripts").mkdir(parents=True, exist_ok=True)
            (source_install_root / "share" / "CodeBlocks" / "scripts" / "gdb_init.gdb").write_text(
                DEV_ONLY_GDB_SOURCE + "\n",
                encoding="utf-8",
            )
            (source_install_root / "codeblocks.exe").write_text("binary", encoding="utf-8")
            (source_install_root / "MinGW" / "share" / "gcc-14.2.0" / "python" / "libstdcxx" / "v6").mkdir(parents=True)
            (source_install_root / "MinGW" / "share" / "gcc-14.2.0" / "python" / "libstdcxx" / "v6" / "printers.py").write_text(
                "printers",
                encoding="utf-8",
            )

            result = prepare_local_release(
                repo_root=repo,
                source_install_root=source_install_root,
                version="v0.1.0",
                output_root=repo / "dist",
            )

            staged_gdb_init = repo / "dist" / "payload" / "CodeBlocks" / "share" / "CodeBlocks" / "scripts" / "gdb_init.gdb"
            self.assertTrue(staged_gdb_init.is_file())
            self.assertIn(PATCHED_GDB_COMMENT, staged_gdb_init.read_text(encoding="utf-8"))
            self.assertTrue((repo / "dist" / "release-assets" / "release-manifest.json").is_file())
            self.assertTrue((repo / "dist" / "release-assets" / "THIRD_PARTY_NOTICES.md").is_file())
            self.assertTrue((repo / "dist" / "release-assets" / "sbom.json").is_file())
            self.assertTrue((repo / "dist" / "release-assets" / "provenance.json").is_file())
            self.assertTrue((repo / "dist" / "release-assets" / "RELEASE_NOTES_v0.1.0.md").is_file())
            self.assertEqual(result["harvested_notice_count"], 1)

            rerun = prepare_local_release(
                repo_root=repo,
                source_install_root=source_install_root,
                version="v0.1.0",
                output_root=repo / "dist",
            )
            self.assertEqual(rerun["harvested_notice_count"], 1)

    def test_prepare_local_release_rejects_missing_codeblocks_exe(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            repo = root / "repo"
            repo.mkdir()
            write_release_input_skeleton(repo, manifest=base_manifest())
            write_materialized_profile_seed(repo)
            (repo / "THIRD_PARTY_NOTICES.md").write_text("policy", encoding="utf-8")
            source_install_root = root / "missing-install"
            source_install_root.mkdir()
            with self.assertRaisesRegex(ValueError, "Code::Blocks executable not found"):
                prepare_local_release(
                    repo_root=repo,
                    source_install_root=source_install_root,
                    version="v0.1.0",
                    output_root=repo / "dist",
                )

    def test_release_manifest_sbom_and_provenance_include_expected_fields(self) -> None:
        manifest = base_manifest()
        release_manifest = build_release_manifest(
            version="v0.1.0",
            payload_manifest=manifest,
            source_install_root=r"C:\Program Files\CodeBlocks",
            source_payload_sha256="abc123",
        )
        self.assertEqual(release_manifest["version"], "v0.1.0")
        self.assertEqual(release_manifest["baseline_source"]["kind"], "local-known-good-install")

        sbom = build_sbom(version="v0.1.0", payload_manifest=manifest, source_payload_sha256="abc123")
        self.assertEqual(sbom["metadata"]["component"]["version"], "v0.1.0")
        self.assertEqual(sbom["components"][0]["hashes"][0]["content"], "abc123")

        provenance = build_provenance(
            version="v0.1.0",
            source_install_root=r"C:\Program Files\CodeBlocks",
            source_payload_sha256="abc123",
        )
        self.assertEqual(provenance["version"], "v0.1.0")
        self.assertEqual(provenance["payload_source"]["sha256"], "abc123")

    def test_render_release_notes_mentions_debugger_and_pretty_printers(self) -> None:
        notes = render_release_notes("v0.1.0", base_manifest())
        self.assertIn("pretty-printer", notes)
        self.assertIn("plug-and-play", notes)
        self.assertIn("GDB: 16.2", notes)

    def test_compose_notice_policy_handles_empty_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            (repo / "THIRD_PARTY_NOTICES.md").write_text("policy", encoding="utf-8")
            text = compose_notice_policy(repo_root=repo, harvested_paths=[], version="v0.1.0")
            self.assertIn("No notice files were harvested.", text)

    def test_main_prepare_local_release_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            repo = root / "repo"
            repo.mkdir()
            write_release_input_skeleton(repo, manifest=base_manifest())
            (repo / "manifests" / "notice_inventory.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "included_patterns": ["printers.py"],
                        "categories": {"runtime_notice": ["printers.py"]},
                    }
                ),
                encoding="utf-8",
            )
            write_materialized_profile_seed(repo)
            (repo / "THIRD_PARTY_NOTICES.md").write_text("policy", encoding="utf-8")

            source_install_root = root / "CodeBlocks"
            (source_install_root / "share" / "CodeBlocks" / "scripts").mkdir(parents=True, exist_ok=True)
            (source_install_root / "share" / "CodeBlocks" / "scripts" / "gdb_init.gdb").write_text(
                DEV_ONLY_GDB_SOURCE + "\n",
                encoding="utf-8",
            )
            (source_install_root / "codeblocks.exe").write_text("binary", encoding="utf-8")
            (source_install_root / "MinGW" / "share" / "gcc-14.2.0" / "python" / "libstdcxx" / "v6").mkdir(parents=True)
            (source_install_root / "MinGW" / "share" / "gcc-14.2.0" / "python" / "libstdcxx" / "v6" / "printers.py").write_text(
                "printers",
                encoding="utf-8",
            )

            rc = main(
                [
                    "prepare-local-release",
                    "--repo-root",
                    str(repo),
                    "--source-install-root",
                    str(source_install_root),
                    "--version",
                    "v0.1.0",
                    "--output-root",
                    str(repo / "dist"),
                ]
            )
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
