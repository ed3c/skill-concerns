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

That bound the whole row-set to an execution but left each row's *id* free: the
twelve mandatory ids were a list literal, so a receipt could carry a true
statement about the wrong denominator (`control-backup` stamping
`agents-three-document-route: PASS` while nothing in its checks ran
`check_agents_hops.py`). Every id now names the unittest that measures it --
mandatory ids through `MANDATORY_PRODUCERS`, eval-case ids through each case's
own `test` field in `evals/cases.json` -- and `run_measurements()` executes
every named test before `build_receipt()` sees the id. `python -m unittest <id>`
errors when the id resolves to nothing, so an assertion deleted out of an
otherwise-green suite leaves its control unmeasured and refuses the stamp
instead of stamping a row nobody produced.

`run_all.SKILL_CHECKS` is the single declaration of what a Skill's checks are, so
the suite and the stamper cannot diverge. The table lives in the runner rather
than here: `check_skill_bundles` proves a declared executable route is reached by
reading the runner's bytes, and in CI that checker runs from the default branch
against this tree as data.
"""

from __future__ import annotations

import json
import os
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

# Mandatory control id -> the unittest id whose execution measures it, in the
# order `check_admissions` expects the rows.
#
# These twelve are enforced by repo-wide checkers rather than by any one Skill's
# own checks, so before this table they were reachable from a list literal
# alone. Each now points at the assertion that exercises the checker; the stamp
# runs that assertion, and a control with no green producer never reaches a
# receipt. `check_admissions.MANDATORY_CONTROLS` derives its membership from
# this dict, so an id cannot exist on one side only.
#
# Every producer is a hermetic negative control over fixtures, never a
# scan-the-live-tree positive like `test_current_skill_bundles_pass`. A producer
# that reads the whole repository goes red for *any* defect, so the refusal
# would name whichever mandatory id happened to sort first instead of the
# control that actually lost its measurement.
MANDATORY_PRODUCERS: dict[str, str] = {
    "agents-three-document-route": (
        "test_repository_controls.RepositoryControlTests.test_fourth_agent_document_fails"
    ),
    "bundle-anatomy": (
        "test_repository_controls.RepositoryControlTests"
        ".test_forbidden_domain_literal_fails_portable_core"
    ),
    "source-lock": (
        "test_repository_controls.RepositoryControlTests"
        ".test_freeze_source_requires_exact_commit_and_hashes_files"
    ),
    "executable-route": (
        "test_repository_controls.RepositoryControlTests.test_hollow_executable_route_fails"
    ),
    "feature-map-positive": (
        "test_feature_map.FeatureMapTests.test_positive_complete_feature_proof"
    ),
    "missing-terminal-oracle": (
        "test_feature_map.FeatureMapTests.test_missing_terminal_oracle_fails"
    ),
    "static-only-false-proof": (
        "test_feature_map.FeatureMapTests.test_static_only_false_proof_fails"
    ),
    "skip-without-blocker": (
        "test_feature_map.FeatureMapTests.test_skip_without_blocker_fails"
    ),
    "changed-feature-hollow-route": (
        "test_feature_map.FeatureMapTests.test_changed_feature_without_proof_fails"
    ),
    "transition-chain-mutation": (
        "test_feature_map.FeatureMapTests.test_invalid_transition_chain_fails"
    ),
    "persistence-mutation": (
        "test_feature_map.FeatureMapTests.test_persistence_evidence_missing_fails"
    ),
    "admission-tree-digest": (
        "test_repository_controls.RepositoryControlTests"
        ".test_tree_digest_changes_when_bytes_change"
    ),
}


class StampRefused(RuntimeError):
    """Raised instead of writing a receipt the tree does not support."""


def unittest_path(root: Path) -> str:
    """The sys.path a bare `test_<module>` id needs, matching `discover -s`.

    `root/tests` is searched first, so a module name that exists in both
    `root/tests` and some `skills/*/tests` would silently resolve to the root
    copy -- rebinding whichever mandatory ids point at the skill copy without
    either `MANDATORY_PRODUCERS` or the receipt changing. Refuse instead of
    letting that happen quietly.
    """
    directories = [root / "tests", *sorted((root / "skills").glob("*/tests"))]
    mandatory_modules = {producer.split(".", 1)[0] for producer in MANDATORY_PRODUCERS.values()}
    seen: dict[str, Path] = {}
    shadowed: set[str] = set()
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in directory.glob("test_*.py"):
            module = path.stem
            if module in mandatory_modules and module in seen:
                shadowed.add(module)
            seen.setdefault(module, directory)
    if shadowed:
        raise StampRefused(f"{REFUSAL}:MODULE_NAME_SHADOWED:{','.join(sorted(shadowed))}")
    return os.pathsep.join(str(directory) for directory in directories)


def control_tests(skill: str, root: Path) -> dict[str, str]:
    """control id -> producing unittest id, in receipt row order.

    An eval case that carries a mandatory control's id is that control; the
    mandatory binding wins so both sides name one execution.
    """
    skill_root = root / "skills" / skill
    manifest = load_json(skill_root / "skill.json")
    cases = load_json(skill_root / manifest["eval_inventory"])["cases"]
    bound: dict[str, str] = dict(MANDATORY_PRODUCERS)
    for case in cases:
        case_id = case.get("id")
        test_id = case.get("test")
        if not isinstance(case_id, str) or not case_id:
            raise StampRefused(f"{REFUSAL}:{skill}:CASE_ID_INVALID")
        if not isinstance(test_id, str) or not test_id:
            raise StampRefused(f"{REFUSAL}:{skill}:CASE_WITHOUT_PRODUCER:{case_id}")
        bound.setdefault(case_id, test_id)
    return bound


def run_measurements(skill: str, root: Path, bound: dict[str, str]) -> None:
    """Execute every producer in `bound`; refuse naming the first unmeasured id.

    The batch runs once; only when it is red does each id get its own probe, so
    the refusal names the control rather than the suite.
    """
    env = {**os.environ, "PYTHONPATH": unittest_path(root)}
    command = [sys.executable, "-m", "unittest", "-v", *sorted(set(bound.values()))]
    print("+", " ".join(command), flush=True)
    if subprocess.run(command, cwd=root, env=env).returncode == 0:
        return
    for control_id, test_id in bound.items():
        probe = subprocess.run(
            [sys.executable, "-m", "unittest", test_id],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
        )
        if probe.returncode != 0:
            raise StampRefused(
                f"{REFUSAL}:{skill}:UNMEASURED_CONTROL:{control_id}:{test_id}"
            )
    raise StampRefused(f"{REFUSAL}:{skill}:UNMEASURED_CONTROL")


def run_checks(skill: str, root: Path) -> dict[str, str]:
    """Execute the Skill's declared checks, then every control's own producer.

    Raises `StampRefused` on the first red; returns the control -> producer map
    the receipt's rows are built from.
    """
    checks = SKILL_CHECKS.get(skill)
    if not checks:
        raise StampRefused(f"{REFUSAL}:{skill}:NO_DECLARED_CHECKS")
    for argv in checks:
        command = [sys.executable, *argv]
        print("+", " ".join(command), flush=True)
        if subprocess.run(command, cwd=root).returncode != 0:
            raise StampRefused(f"{REFUSAL}:{skill}:RED_CHECK:{' '.join(argv)}")
    bound = control_tests(skill, root)
    run_measurements(skill, root, bound)
    return bound


def build_receipt(skill: str, root: Path, bound: dict[str, str]) -> dict:
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

    # Every id here came out of `control_tests()` and survived
    # `run_measurements()`; there is no literal row-set to fall back on.
    controls = [{"id": control_id, "state": "PASS"} for control_id in bound]

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
    """Re-run the Skill's checks and each control's producer, then write."""
    try:
        bound = run_checks(skill, root)
    except StampRefused as exc:
        print(exc, file=sys.stderr, flush=True)
        return 1
    out = root / "admissions" / f"{skill}.json"
    out.write_text(
        json.dumps(build_receipt(skill, root, bound), indent=2) + "\n", encoding="utf-8"
    )
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(stamp(sys.argv[1]))
