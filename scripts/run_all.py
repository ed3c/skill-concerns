#!/usr/bin/env python3
"""Run every repository and Skill admission control."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

DISCOVER = ("-m", "unittest", "discover", "-p", "test_*.py", "-v", "-s")

# Skill name -> the checks that must be green for that bundle.
#
# `admission_stamp.stamp()` re-runs this Skill's row before it will write a
# receipt, so the suite and the stamper execute the same argv and cannot
# diverge. The table stays here, in the runner, because
# `check_skill_bundles.EXECUTABLE_ROUTE_HOLLOW` reads this file's bytes to prove
# a declared executable route is actually reached -- and in CI that checker runs
# from the default branch against this tree as data. Moving the argv out of the
# runner's text blinds that gate.
SKILL_CHECKS: dict[str, tuple[tuple[str, ...], ...]] = {
    "feature-map-engineering": (
        (
            "skills/feature-map-engineering/scripts/validate_feature_map.py",
            "--map",
            "skills/feature-map-engineering/fixtures/valid/feature-map.json",
            "--plan",
            "skills/feature-map-engineering/fixtures/valid/verification-plan.json",
        ),
        (
            "skills/feature-map-engineering/scripts/coverage_diff.py",
            "--old",
            "skills/feature-map-engineering/fixtures/valid/feature-map.json",
            "--new",
            "skills/feature-map-engineering/fixtures/valid/feature-map.json",
        ),
        (
            "skills/feature-map-engineering/scripts/validate_feature_map.py",
            "--map",
            "docs/features/skill-admission/feature-map.json",
            "--plan",
            "docs/features/skill-admission/verification-plan.json",
        ),
        (*DISCOVER, "skills/feature-map-engineering/tests"),
    ),
    "control-noodle": (
        (
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
        ),
        (*DISCOVER, "skills/control-noodle/tests"),
    ),
    "spatial-loop-grounded": (
        ("skills/spatial-loop-grounded/scripts/validate_spatial_loop_grounded.py",),
        (*DISCOVER, "skills/spatial-loop-grounded/tests"),
    ),
    "control-code-intel": (
        ("skills/control-code-intel/scripts/validate_control_code_intel.py",),
        (*DISCOVER, "skills/control-code-intel/tests"),
    ),
    "control-backup": (
        ("skills/control-backup/scripts/validate_control_backup.py",),
        (*DISCOVER, "skills/control-backup/tests"),
    ),
    "context-closure-engineering": (
        ("skills/context-closure-engineering/scripts/validate_context_closure_engineering.py",),
        (*DISCOVER, "skills/context-closure-engineering/tests"),
    ),
    "dynamic-workflow": (
        ("skills/dynamic-workflow/scripts/validate_dynamic_workflow.py",),
        (*DISCOVER, "skills/dynamic-workflow/tests"),
    ),
    "arrival-engineering": (
        ("skills/arrival-engineering/scripts/validate_arrival_engineering.py",),
        (*DISCOVER, "skills/arrival-engineering/tests"),
    ),
    "red-team": (
        ("skills/red-team/scripts/validate_red_team.py",),
        (*DISCOVER, "skills/red-team/tests"),
    ),
    "shadow-architect": (
        ("skills/shadow-architect/scripts/validate_shadow_architect.py",),
        (*DISCOVER, "skills/shadow-architect/tests"),
    ),
}


# The repository-wide gates, in the order this runner executes them. ONE
# declaration, for the same reason `SKILL_CHECKS` is one: the cadence sweep
# drives these too and used to carry its own hand-typed copy, which had already
# drifted - `check_receipt_provenance.py` ran here and never there, so that
# sweep reported the repository gates green having never run one of them, which
# is the absence-read-as-clean shape this repository admits skills to catch
# (ed3c/skill-concerns#102). Every gate takes `--root`, which is what lets the
# sweep run this same tuple against a candidate tree.
#
# Named here and not there, in that direction only: the sweep is N-class and no
# script in this directory may name it (`test_sweep_gates_nothing`).
REPO_GATES: tuple[str, ...] = (
    "check_agents_hops.py",
    "check_skill_bundles.py",
    "check_admissions.py",
    "check_receipt_provenance.py",
    "check_second_arrival_ceiling.py",
)


def run(*args: str) -> None:
    command = [PYTHON, *args]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    run("-m", "compileall", "-q", "scripts", "tests", "skills")
    for gate in REPO_GATES:
        run(f"scripts/{gate}")
    run("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v")
    for checks in SKILL_CHECKS.values():
        for argv in checks:
            run(*argv)
    print("skill-concerns: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
