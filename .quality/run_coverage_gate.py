#!/usr/bin/env python3
"""Gate 3 runner: unittest suite under coverage, then enforce 100% line+branch.

Invoked by the `coverage-100` pre-commit hook (lean 6-gate charter). Lives under
.quality/ (NOT scripts/) so it is outside the .coveragerc `source = scripts`
scope and does not itself need coverage. Mirrors scripts/verify's coverage steps
but stops at the 100% report (the verify script does the full release pipeline).
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RCFILE = "--rcfile=.coveragerc"


def _run(args: list[str]) -> int:
    return subprocess.call([sys.executable, "-m", "coverage", *args], cwd=REPO_ROOT)  # noqa: S603


def main() -> int:
    (REPO_ROOT / ".coverage").unlink(missing_ok=True)
    rc = _run(["run", RCFILE, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
    if rc != 0:
        return rc
    return _run(["report", RCFILE, "--fail-under=100", "--show-missing"])


if __name__ == "__main__":
    raise SystemExit(main())
