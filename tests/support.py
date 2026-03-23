from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONF = "default.conf"
DEFAULT_KEYBINDINGS_CONF = "default.cbKeyBinder20.conf"
CODESNIPPETS_INI = "codesnippets.ini"
PROFILE_FILE_NAMES = [DEFAULT_CONF, DEFAULT_KEYBINDINGS_CONF, CODESNIPPETS_INI]
LICENSE_PATTERN = "LICENSE*"
GDBINIT_PATTERN = "gdbinit"
GDB_PY_PATTERN = "*.gdb.py"
CODEBLOCKS_INSTALL_ROOT = r"C:\Program Files\CodeBlocks"
STABLE_INSTALL_ROOT = r"C:\Program Files\CodeBlocks Stable Toolchain Edition"
APPDATA_PROFILE_ROOT = r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks"
MANAGED_PROFILE_ROOT = r"C:\Users\Prekzursil\AppData\Roaming\CodeBlocks Stable Toolchain Edition"
TOOLCHAIN_ROOT = STABLE_INSTALL_ROOT + r"\MinGW"
TOOLCHAIN_PYTHON_ROOT = TOOLCHAIN_ROOT + r"\share\gcc-14.2.0\python"


def base_manifest() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "repo_name": "codeblocks-pretty-prints-stable",
        "edition_name": "Code::Blocks Stable Toolchain Edition",
        "product_name": "Code::Blocks",
        "install_scope": "machine-wide",
        "host_architecture": "x64",
        "target_architectures": ["x86", "x64"],
        "current_official_install_root": CODEBLOCKS_INSTALL_ROOT,
        "edition_install_root": STABLE_INSTALL_ROOT,
        "current_profile_root": APPDATA_PROFILE_ROOT,
        "managed_profile_root": MANAGED_PROFILE_ROOT,
        "toolchain_relative_root": "MinGW",
        "toolchain_python_relative_root": r"share\gcc-14.2.0\python",
        "bundled_toolchain": {
            "gcc_version": "14.2.0",
            "gdb_version": "16.2",
            "family": "mingw-w64-ucrt-posix-seh",
        },
        "profile_sources": PROFILE_FILE_NAMES,
        "profile_outputs": PROFILE_FILE_NAMES,
        "notice_name_patterns": [
            LICENSE_PATTERN,
            GDBINIT_PATTERN,
            GDB_PY_PATTERN,
        ],
        "profile_rewrites": {
            "debugger_executable": TOOLCHAIN_ROOT + r"\bin\gdb.exe",
            "debugger_python_root": TOOLCHAIN_PYTHON_ROOT,
            "toolchain_root": TOOLCHAIN_ROOT,
            "profile_root": MANAGED_PROFILE_ROOT,
        },
    }


def write_profile_bundle(root: Path, default_conf: str, codesnippets_ini: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / DEFAULT_CONF).write_text(default_conf, encoding="utf-8")
    (root / DEFAULT_KEYBINDINGS_CONF).write_text("{}", encoding="utf-8")
    (root / CODESNIPPETS_INI).write_text(codesnippets_ini, encoding="utf-8")


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
                "included_patterns": [LICENSE_PATTERN],
                "categories": {"license": [LICENSE_PATTERN]},
            }
        ),
        encoding="utf-8",
    )
    return payload_manifest


def write_materialized_profile_seed(repo: Path, *, content: str = "seed") -> None:
    profile_seed_root = repo / "overlay" / "profile-seed"
    profile_seed_root.mkdir(parents=True, exist_ok=True)
    for name in PROFILE_FILE_NAMES:
        (profile_seed_root / name).write_text(content, encoding="utf-8")
    (repo / "overlay" / "profile-replacements.json").write_text(
        json.dumps({"schema_version": 1, "replacements": []}),
        encoding="utf-8",
    )
