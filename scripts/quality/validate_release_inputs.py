from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.codeblocks_stable import validate_release_inputs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the release inputs for the curated Code::Blocks package.")
    parser.add_argument("repo_root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = validate_release_inputs(args.repo_root)
    if args.output is not None:
        payload = {
            "notice_count": result["notice_count"],
            "manifest_name": result["manifest"]["repo_name"],
            "overlay_seed_name": result["overlay_seed"]["seed_name"],
        }
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

