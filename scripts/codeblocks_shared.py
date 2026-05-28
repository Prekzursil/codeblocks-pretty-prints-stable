"""Shared helpers for loading, writing, and validating manifest data."""
from __future__ import annotations

import dataclasses
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any


@dataclasses.dataclass(frozen=True)
class NoticeEntry:
    """A single redistributable notice file and its category."""

    path: str
    category: str


def load_json_document(path: str | Path) -> dict[str, Any]:
    """Load a JSON object from ``path`` and verify it is a mapping."""
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{file_path} must contain a JSON object")
    return payload


def write_json_document(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write ``payload`` to ``path`` as pretty-printed UTF-8 JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(dict(payload), indent=2) + "\n", encoding="utf-8")


def as_windows_string(value: str | Path) -> str:
    """Return ``value`` with POSIX separators rewritten as backslashes."""
    return str(value).replace("/", "\\")


def expand_manifest_path(value: str | Path) -> Path:
    """Expand environment variables in a Windows-style manifest path."""
    return Path(os.path.expandvars(as_windows_string(value)))


def ensure_str_list(value: Any, label: str) -> list[str]:
    """Validate ``value`` is a non-empty list of non-blank strings."""
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{label} must be a non-empty list of strings")
    return [item.strip() for item in value]


def require_non_empty_string(value: Any, label: str) -> str:
    """Validate ``value`` is a non-blank string and return it stripped."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()
