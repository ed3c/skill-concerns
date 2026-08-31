#!/usr/bin/env python3
"""Run every repository and Skill admission control."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(*args: str) -> None:
    command = [PYTHON, *args]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("-m", "compileall", "-q", "scripts", "tests", "skills")
    run("scripts/check_agents_hops.py")
    run("scripts/check_skill_bundles.py")
    run("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v")
    run(
        "-m",
        "unittest",
        "discover",
        "-s",
        "skills/feature-map-engineering/tests",
        "-p",
        "test_*.py",
        "-v",
    )
    run("skills/spatial-loop-grounded/scripts/validate_spatial_loop_grounded.py")
    run(
        "-m",
        "unittest",
        "discover",
        "-s",
        "skills/spatial-loop-grounded/tests",
        "-p",
        "test_*.py",
        "-v",
    )
    run(
        "-m",
        "unittest",
        "discover",
        "-s",
        "skills/control-noodle/tests",
        "-p",
        "test_*.py",
        "-v",
    )
    run(
        "skills/feature-map-engineering/scripts/validate_feature_map.py",
        "--map",
        "skills/feature-map-engineering/fixtures/valid/feature-map.json",
        "--plan",
        "skills/feature-map-engineering/fixtures/valid/verification-plan.json",
    )
    run(
        "skills/feature-map-engineering/scripts/coverage_diff.py",
        "--old",
        "skills/feature-map-engineering/fixtures/valid/feature-map.json",
        "--new",
        "skills/feature-map-engineering/fixtures/valid/feature-map.json",
    )
    run(
        "skills/control-noodle/scripts/validate_control_noodle.py",
        "--composition",
        "skills/control-noodle/domain/composition.json",
        "--feature-map",
        "skills/control-noodle/domain/feature-map.json",
        "--code-map",
        "skills/control-noodle/domain/code-map.json",
        "--mapping",
        "skills/control-noodle/domain/feature-code-map.json",
        "--adapter",
        "skills/control-noodle/domain/domain-adapter.json",
        "--change-set",
        "skills/control-noodle/fixtures/valid/change-set.json",
        "--plan",
        "skills/control-noodle/fixtures/valid/verification-plan.json",
        "--procedure-admission",
        "admissions/feature-map-engineering.json",
        "--source-lock",
        "intake/control-noodle/source-lock.json",
    )
    run("scripts/check_admissions.py")
    print("skill-concerns: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
