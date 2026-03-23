from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.codeblocks_notices import collect_notice_inventory
from scripts.codeblocks_profile import validate_profile_overlay_contract
from scripts.codeblocks_shared import ensure_str_list, load_json_document, require_non_empty_string


def require_manifest_keys(manifest: Mapping[str, Any], required_keys: Sequence[str]) -> None:
    missing = [key for key in required_keys if key not in manifest]
    if missing:
        raise ValueError(f"manifest missing keys: {', '.join(missing)}")


def validate_manifest_literals(manifest: Mapping[str, Any]) -> None:
    expected_literals = {
        "schema_version": 1,
        "install_scope": "machine-wide",
        "host_architecture": "x64",
    }
    for key, expected in expected_literals.items():
        if manifest[key] != expected:
            raise ValueError(f"{key} must be {expected}")


def validate_bundled_toolchain(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError("bundled_toolchain must be a JSON object")
    for key in ("gcc_version", "gdb_version", "family"):
        require_non_empty_string(payload.get(key), f"bundled_toolchain.{key}")


def validate_profile_rewrites(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError("profile_rewrites must be a JSON object")
    for key in ("debugger_executable", "debugger_python_root", "toolchain_root", "profile_root"):
        require_non_empty_string(payload.get(key), f"profile_rewrites.{key}")


def validate_payload_manifest(manifest: Mapping[str, Any]) -> None:
    required_keys = (
        "schema_version",
        "repo_name",
        "edition_name",
        "product_name",
        "install_scope",
        "host_architecture",
        "target_architectures",
        "current_official_install_root",
        "edition_install_root",
        "current_profile_root",
        "managed_profile_root",
        "toolchain_relative_root",
        "toolchain_python_relative_root",
        "bundled_toolchain",
        "profile_sources",
        "profile_outputs",
        "notice_name_patterns",
        "profile_rewrites",
    )
    require_manifest_keys(manifest, required_keys)
    validate_manifest_literals(manifest)
    for key in ("repo_name", "edition_name", "product_name"):
        require_non_empty_string(manifest[key], key)
    if not {"x86", "x64"}.issubset(set(ensure_str_list(manifest["target_architectures"], "target_architectures"))):
        raise ValueError("target_architectures must include x86 and x64")
    validate_bundled_toolchain(manifest["bundled_toolchain"])
    ensure_str_list(manifest["profile_sources"], "profile_sources")
    ensure_str_list(manifest["profile_outputs"], "profile_outputs")
    ensure_str_list(manifest["notice_name_patterns"], "notice_name_patterns")
    validate_profile_rewrites(manifest["profile_rewrites"])


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = load_json_document(path)
    validate_payload_manifest(manifest)
    return manifest


def release_input_checks(
    notices_manifest: Mapping[str, Any],
    overlay_seed: Mapping[str, Any],
    profile_state: Mapping[str, Any],
) -> list[tuple[bool, str]]:
    return [
        (notices_manifest.get("schema_version") == 1, "notice_inventory schema_version must be 1"),
        (isinstance(notices_manifest.get("included_patterns"), list), "notice_inventory included_patterns must be a list"),
        (overlay_seed.get("schema_version") == 1, "overlay profile_seed schema_version must be 1"),
        (bool(profile_state["profile_seed_root"].is_dir()), "materialized profile seed directory is missing"),
        (
            not profile_state["missing_files"],
            f"profile seed is missing files: {', '.join(profile_state['missing_files'])}",
        ),
        (bool(profile_state["replacements_path"].is_file()), "profile seed overlay contract is missing"),
        (
            isinstance(overlay_seed.get("debugger_init_commands"), list) and bool(overlay_seed["debugger_init_commands"]),
            "overlay profile_seed debugger_init_commands must be a non-empty list",
        ),
        (profile_state["notice_count"] > 0, "notice inventory is empty"),
    ]


def validate_release_inputs(repo_root: str | Path) -> dict[str, Any]:
    repo = Path(repo_root)
    manifest = load_manifest(repo / "manifests" / "codeblocks_stable_toolchain.json")
    notices_manifest = load_json_document(repo / "manifests" / "notice_inventory.json")
    overlay_seed = load_json_document(repo / "overlay" / "profile_seed.json")
    profile_seed_root = repo / "overlay" / "profile-seed"
    replacements_path = repo / "overlay" / "profile-replacements.json"
    notices = collect_notice_inventory(repo, notices_manifest)
    expected_outputs = ensure_str_list(manifest["profile_outputs"], "profile_outputs")
    missing_files = [name for name in expected_outputs if not (profile_seed_root / name).is_file()]
    profile_state = {
        "profile_seed_root": profile_seed_root,
        "replacements_path": replacements_path,
        "missing_files": missing_files,
        "notice_count": len(notices),
    }

    for condition, message in release_input_checks(
        notices_manifest,
        overlay_seed,
        profile_state,
    ):
        if not condition:
            raise ValueError(message)

    validate_profile_overlay_contract(load_json_document(replacements_path))
    return {
        "manifest": manifest,
        "notice_count": len(notices),
        "notices": notices,
        "overlay_seed": overlay_seed,
    }
