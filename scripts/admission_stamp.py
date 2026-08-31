#!/usr/bin/env python3
"""The one admission-stamp surface every Skill's `gen_admission.py` calls.

A receipt claims `PASS` for every mandatory control and every eval case of its
Skill. Nothing used to execute before those rows were written, so the invariant
"a stamped PASS was measured" was carried by operator sequencing prose.

`stamp()` re-runs the Skill's own declared checks -- the exact argv
`scripts/run_all.py` executes for that Skill, validator plus unittest discovery
-- in this process and REFUSES to write when any of them is red. The refusal is
structural: `run_checks()` returns before `build_receipt()` is ever called, so a
red tree cannot produce receipt bytes.

`SKILL_CHECKS` is the single declaration of what a Skill's checks are;
`scripts/run_all.py` runs the same table, so the suite and the stamper can never
diverge.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from common import (
    REPO_ROOT,
    digest_entries,
    load_json,
    regular_files,
    sha256_file,
    tree_digest,
)


REFUSAL = "ADMISSION_STAMP_REFUSED"

# Kept in the order `check_admissions.MANDATORY_CONTROLS` requires membership for.
MANDATORY_CONTROLS = (
    "agents-three-document-route",
    "bundle-anatomy",
    "source-lock",
    "executable-route",
    "feature-map-positive",
    "missing-terminal-oracle",
    "static-only-false-proof",
    "skip-without-blocker",
    "changed-feature-hollow-route",
    "transition-chain-mutation",
    "persistence-mutation",
    "admission-tree-digest",
)

DISCOVER = ("-m", "unittest", "discover", "-p", "test_*.py", "-v", "-s")

# Skill name -> the checks that must be green before its receipt may be written.
# `scripts/run_all.py` executes this same table; `tests/test_admission_stamp.py`
# asserts every registered Skill has an entry.
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
}


class StampRefused(RuntimeError):
    """Raised instead of writing a receipt the tree does not support."""


def run_checks(skill: str, root: Path) -> None:
    """Execute the Skill's declared checks. Raise `StampRefused` on the first red."""
    checks = SKILL_CHECKS.get(skill)
    if not checks:
        raise StampRefused(f"{REFUSAL}:{skill}:NO_DECLARED_CHECKS")
    for argv in checks:
        command = [sys.executable, *argv]
        print("+", " ".join(command), flush=True)
        if subprocess.run(command, cwd=root).returncode != 0:
            raise StampRefused(f"{REFUSAL}:{skill}:RED_CHECK:{' '.join(argv)}")


def build_receipt(skill: str, root: Path) -> dict:
    skill_root = root / "skills" / skill
    manifest = load_json(skill_root / "skill.json")
    lock = root / "intake" / skill / "source-lock.json"

    subject_files = digest_entries(root, regular_files(skill_root))

    contract_files = []
    for relative in manifest["shared_contracts"]:
        path = (skill_root / relative).resolve()
        contract_files.append(
            {
                "path": path.relative_to(root.resolve()).as_posix(),
                "sha256": sha256_file(path),
            }
        )

    cases = load_json(skill_root / manifest["eval_inventory"])["cases"]
    # An eval case may carry a mandatory control's id; that is the same control,
    # and `check_admissions` rejects the row twice over.
    controls: list[dict[str, str]] = []
    seen: set[str] = set()
    for control_id in (*MANDATORY_CONTROLS, *(case["id"] for case in cases)):
        if control_id not in seen:
            seen.add(control_id)
            controls.append({"id": control_id, "state": "PASS"})

    return {
        "schema_version": 1,
        "skill": skill,
        "status": "ADMITTED",
        "source_lock": {
            "path": lock.relative_to(root).as_posix(),
            "sha256": sha256_file(lock),
        },
        "subject_files": subject_files,
        "skill_tree_sha256": tree_digest(subject_files),
        "contract_files": contract_files,
        "controls": controls,
        "evidence_ceiling": "L3_HERMETIC",
        "not_claimed": ["L4_MATCHED_LIVE_RUNTIME", "L5_DELIVERY_AND_PRODUCTION"],
        "authoring_command": "python3 scripts/run_all.py",
        "hosted_evidence": "READ_FROM_GITHUB",
    }


def stamp(skill: str, root: Path = REPO_ROOT) -> int:
    """Re-run the Skill's checks, then write its receipt. Refuse when red."""
    try:
        run_checks(skill, root)
    except StampRefused as exc:
        print(exc, file=sys.stderr, flush=True)
        return 1
    out = root / "admissions" / f"{skill}.json"
    out.write_text(json.dumps(build_receipt(skill, root), indent=2) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(stamp(sys.argv[1]))
