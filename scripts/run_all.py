#!/usr/bin/env python3
"""Run every repository and Skill admission control."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from admission_stamp import SKILL_CHECKS  # noqa: E402


def run(*args: str) -> None:
    command = [PYTHON, *args]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("-m", "compileall", "-q", "scripts", "tests", "skills")
    run("scripts/check_agents_hops.py")
    run("scripts/check_skill_bundles.py")
    run("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v")
    # One table, two consumers: this suite and `admission_stamp.stamp()` execute
    # the same argv, so a Skill cannot be checked here and unchecked at stamp time.
    for checks in SKILL_CHECKS.values():
        for argv in checks:
            run(*argv)
    run("scripts/check_admissions.py")
    print("skill-concerns: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
