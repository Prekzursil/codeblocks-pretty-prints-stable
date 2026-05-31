"""Shared helpers for loading, writing, and validating manifest data."""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def dispatch_cli(
    parser: argparse.ArgumentParser, argv: Sequence[str] | None
) -> int:
    """Parse ``argv`` with ``parser`` and dispatch to the chosen subcommand.

    Each subcommand registered on ``parser`` is expected to set a ``func``
    default that accepts the parsed namespace and returns an exit code. The
    shared logic lives here so the script entrypoints do not duplicate the
    parse-and-dispatch sequence.
    """
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


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


def _is_non_blank_string(item: Any) -> bool:
    """Return ``True`` when ``item`` is a string with non-whitespace content."""
    return isinstance(item, str) and bool(item.strip())


def ensure_str_list(value: Any, label: str) -> list[str]:
    """Validate ``value`` is a non-empty list of non-blank strings."""
    if (
        not isinstance(value, list)
        or not value
        or not all(_is_non_blank_string(item) for item in value)
    ):
        raise ValueError(f"{label} must be a non-empty list of strings")
    return [item.strip() for item in value]


def require_non_empty_string(value: Any, label: str) -> str:
    """Validate ``value`` is a non-blank string and return it stripped."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()
