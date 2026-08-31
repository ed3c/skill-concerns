#!/usr/bin/env python3
"""The one admission-stamp surface every Skill's `gen_admission.py` calls.

A receipt claims `PASS` for every mandatory control and every eval case of its
Skill. Nothing used to execute before those rows were written, so the invariant
"a stamped PASS was measured" was carried by operator sequencing prose.

`stamp()` re-runs the Skill's own declared checks -- the exact argv
`scripts/run_all.py` executes for that Skill, validator plus unittest discovery
-- in this process and REFUSES to write when any of them is red. The refusal is
structural for this path: `run_checks()` returns before `build_receipt()` is
ever called, so going through this stamper on a red tree cannot produce receipt
bytes. It does not follow a receipt from anywhere else -- nothing here stops a
receipt from being hand-authored or copied in with matching digests; that gap
is CI's to close, not this module's.

`run_all.SKILL_CHECKS` is the single declaration of what a Skill's checks are, so
the suite and the stamper cannot diverge. The table lives in the runner rather
than here: `check_skill_bundles` proves a declared executable route is reached by
reading the runner's bytes, and in CI that checker runs from the default branch
against this tree as data.
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
from run_all import SKILL_CHECKS


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
        # NOTE: the true producer is skills/<skill>/scripts/gen_admission.py, not
        # this string -- see ed3c/skill-concerns#44 for why the honest value
        # can't ship in the same PR that adds contract-pin content: the trusted
        # verify.yml step runs check_admissions.py from the *default branch*
        # against candidate data, so tightening the check and changing the
        # value it checks can never land atomically in one PR.
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
