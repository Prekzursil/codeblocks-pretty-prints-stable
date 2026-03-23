from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def base_manifest() -> dict[str, Any]:
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


def write_profile_bundle(root: Path, default_conf: str, codesnippets_ini: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "default.conf").write_text(default_conf, encoding="utf-8")
    (root / "default.cbKeyBinder20.conf").write_text("{}", encoding="utf-8")
    (root / "codesnippets.ini").write_text(codesnippets_ini, encoding="utf-8")


def write_release_input_skeleton(repo: Path, *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    payload_manifest = manifest or base_manifest()
    (repo / "manifests").mkdir(parents=True, exist_ok=True)
    (repo / "overlay").mkdir(parents=True, exist_ok=True)
    (repo / "LICENSE.txt").write_text("license", encoding="utf-8")
    (repo / "manifests" / "codeblocks_stable_toolchain.json").write_text(
        json.dumps(payload_manifest),
        encoding="utf-8",
    )
    (repo / "manifests" / "notice_inventory.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "included_patterns": ["LICENSE*"],
                "categories": {"license": ["LICENSE*"]},
            }
        ),
        encoding="utf-8",
    )
    return payload_manifest


def write_materialized_profile_seed(repo: Path, *, content: str = "seed") -> None:
    profile_seed_root = repo / "overlay" / "profile-seed"
    profile_seed_root.mkdir(parents=True, exist_ok=True)
    for name in base_manifest()["profile_outputs"]:
        (profile_seed_root / name).write_text(content, encoding="utf-8")
    (repo / "overlay" / "profile-replacements.json").write_text(
        json.dumps({"schema_version": 1, "replacements": []}),
        encoding="utf-8",
    )
