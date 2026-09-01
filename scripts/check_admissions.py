#!/usr/bin/env python3
"""Validate complete content-bound source locks and admission receipts.

TIGHTENING HAZARD -- read before narrowing any field check here.

`verify.yml` runs this file from the **default branch** against the candidate
tree. A pull request that tightens a check *and* changes the value that check
reads is graded by the *old*, unmerged copy of this file, which still demands
the old value: such a PR can never go green on its own trust model, no matter
how correct it is. `check_skill_bundles.EXECUTABLE_ROUTE_HOLLOW` carries the
same hazard and names it in `run_all.py`'s docstring; nothing named it here
until ed3c/skill-concerns#44 hit it head-on (PR #43 failed with five
`AUTHORING_COMMAND_INVALID` rows for exactly this reason).

Split any such change into two landings: first loosen this file to accept both
the old and new value, with no data change, so the trusted copy on the default
branch accepts either; then change the data and narrow back down. The
`authoring_command` check below is currently mid-split -- it accepts both.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
from typing import Any

from admission_stamp import MANDATORY_PRODUCERS
from common import (
    EVIDENCE_LEVELS,
    REPO_ROOT,
    compare_digest_entries,
    digest_entries,
    load_json,
    print_result,
    regular_files,
    safe_repo_path,
    sha256_file,
    tree_digest,
)


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
# One declaration, two readers: the stamper writes a mandatory row only after
# running that id's producer, and this gate requires the same twelve ids. A
# second literal here let the two sets drift silently (ed3c/skill-concerns#40).
MANDATORY_CONTROLS = set(MANDATORY_PRODUCERS)


def authoring_commands(name: str) -> set[str]:
    """The commands a receipt for `name` may claim as its producer.

    `python3 scripts/run_all.py` is what every committed receipt says today and
    it names a command that structurally cannot have produced those bytes --
    `run_all.py` never calls `gen_admission.py`. The honest value is the
    per-Skill delegate. Both are accepted during the split described in this
    module's docstring; the second landing drops the run_all value and
    regenerates the five receipts (ed3c/skill-concerns#44).
    """
    return {
        "python3 scripts/run_all.py",
        f"python3 skills/{name}/scripts/gen_admission.py",
    }


def produced_control_ids(skill_root: Path) -> set[str]:
    """Every control id this Skill's tree can produce: mandatory + its own cases."""
    produced = set(MANDATORY_PRODUCERS)
    try:
        manifest = load_json(skill_root / "skill.json")
        inventory = load_json(skill_root / manifest["eval_inventory"])
    except (ValueError, KeyError, TypeError):
        return produced
    cases = inventory.get("cases") if isinstance(inventory, dict) else None
    if isinstance(cases, list):
        for case in cases:
            if isinstance(case, dict) and isinstance(case.get("id"), str):
                produced.add(case["id"])
    return produced


def validate_source_lock(root: Path, lock_path: Path, lock: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(lock, dict):
        return [f"SOURCE_LOCK_NOT_OBJECT:{lock_path}"]
    if lock.get("schema_version") != 1:
        errors.append(f"SOURCE_LOCK_SCHEMA_VERSION:{lock_path}")
    if not isinstance(lock.get("skill"), str):
        errors.append(f"SOURCE_LOCK_SKILL_INVALID:{lock_path}")
    source_kind = lock.get("source_kind")
    if source_kind not in {"git", "owner-design-brief"}:
        errors.append(f"SOURCE_LOCK_KIND_INVALID:{lock_path}:{source_kind}")

    if source_kind == "git":
        if not isinstance(lock.get("repository"), str) or not lock.get("repository"):
            errors.append(f"SOURCE_LOCK_REPOSITORY_MISSING:{lock_path}")
        if not isinstance(lock.get("commit"), str) or not HEX40.fullmatch(
            lock.get("commit", "")
        ):
            errors.append(f"SOURCE_LOCK_COMMIT_INVALID:{lock_path}")
        if not isinstance(lock.get("source_path"), str):
            errors.append(f"SOURCE_LOCK_SOURCE_PATH_INVALID:{lock_path}")
    else:
        if lock.get("commit") is not None:
            errors.append(f"DESIGN_BRIEF_COMMIT_FORBIDDEN:{lock_path}")

    locked_files = lock.get("locked_files")
    if not isinstance(locked_files, list) or not locked_files:
        errors.append(f"SOURCE_LOCK_FILES_EMPTY:{lock_path}")
    else:
        seen: set[str] = set()
        for entry in locked_files:
            if not isinstance(entry, dict):
                errors.append(f"SOURCE_LOCK_FILE_NOT_OBJECT:{lock_path}")
                continue
            path_value = entry.get("path")
            digest = entry.get("sha256")
            if not isinstance(path_value, str):
                errors.append(f"SOURCE_LOCK_FILE_PATH_INVALID:{lock_path}")
                continue
            if path_value in seen:
                errors.append(f"SOURCE_LOCK_FILE_DUPLICATE:{path_value}")
            seen.add(path_value)
            try:
                path = safe_repo_path(root, path_value)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not path.is_file():
                errors.append(f"SOURCE_LOCK_FILE_ABSENT:{path_value}")
            elif digest != sha256_file(path):
                errors.append(f"SOURCE_LOCK_FILE_DRIFT:{path_value}")
            if not isinstance(digest, str) or not HEX64.fullmatch(digest):
                errors.append(f"SOURCE_LOCK_DIGEST_INVALID:{path_value}")

    references = lock.get("method_references")
    if not isinstance(references, list):
        errors.append(f"METHOD_REFERENCES_INVALID:{lock_path}")
    else:
        for position, reference in enumerate(references):
            if not isinstance(reference, dict):
                errors.append(f"METHOD_REFERENCE_NOT_OBJECT:{position}")
                continue
            for key in ("repository", "path"):
                if not isinstance(reference.get(key), str) or not reference.get(key):
                    errors.append(f"METHOD_REFERENCE_FIELD_INVALID:{position}:{key}")
            for key in ("commit", "blob_sha"):
                value = reference.get(key)
                if not isinstance(value, str) or not HEX40.fullmatch(value):
                    errors.append(f"METHOD_REFERENCE_HEX_INVALID:{position}:{key}")

    return errors


def check(root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_json(root / "registry.json")
    except ValueError as exc:
        return [str(exc)]
    if not isinstance(registry, dict):
        return ["REGISTRY_NOT_OBJECT"]

    policy = registry.get("policy", {})
    minimum = policy.get("minimum_admission_level")
    if minimum not in EVIDENCE_LEVELS:
        errors.append(f"MINIMUM_EVIDENCE_INVALID:{minimum}")
        minimum_index = len(EVIDENCE_LEVELS)
    else:
        minimum_index = EVIDENCE_LEVELS.index(minimum)

    rows = registry.get("skills")
    if not isinstance(rows, list):
        return errors + ["REGISTRY_SKILLS_NOT_LIST"]

    for row in rows:
        if not isinstance(row, dict):
            errors.append("REGISTRY_SKILL_ROW_NOT_OBJECT")
            continue
        name = row.get("name")
        if row.get("status") != "ADMITTED":
            errors.append(f"REGISTRY_SKILL_NOT_ADMITTED:{name}")
        skill_path_value = row.get("path")
        admission_path_value = row.get("admission")
        source_lock_path_value = row.get("source_lock")
        if not all(
            isinstance(value, str)
            for value in (skill_path_value, admission_path_value, source_lock_path_value)
        ):
            errors.append(f"REGISTRY_ADMISSION_PATH_INVALID:{name}")
            continue

        try:
            skill_root = safe_repo_path(root, skill_path_value)
            admission_path = safe_repo_path(root, admission_path_value)
            source_lock_path = safe_repo_path(root, source_lock_path_value)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if not admission_path.is_file():
            errors.append(f"ADMISSION_RECEIPT_ABSENT:{name}")
            continue
        if not source_lock_path.is_file():
            errors.append(f"SOURCE_LOCK_ABSENT:{name}")
            continue

        try:
            admission = load_json(admission_path)
            source_lock = load_json(source_lock_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        errors.extend(validate_source_lock(root, source_lock_path, source_lock))

        if not isinstance(admission, dict):
            errors.append(f"ADMISSION_NOT_OBJECT:{name}")
            continue
        if admission.get("schema_version") != 1:
            errors.append(f"ADMISSION_SCHEMA_VERSION:{name}")
        if admission.get("skill") != name:
            errors.append(f"ADMISSION_SKILL_MISMATCH:{name}")
        if admission.get("status") != "ADMITTED":
            errors.append(f"ADMISSION_STATUS_INVALID:{name}")

        source_subject = admission.get("source_lock")
        if not isinstance(source_subject, dict):
            errors.append(f"ADMISSION_SOURCE_LOCK_INVALID:{name}")
        else:
            if source_subject.get("path") != source_lock_path_value:
                errors.append(f"ADMISSION_SOURCE_LOCK_PATH_MISMATCH:{name}")
            if source_subject.get("sha256") != sha256_file(source_lock_path):
                errors.append(f"ADMISSION_SOURCE_LOCK_DIGEST_DRIFT:{name}")

        try:
            actual_subject = digest_entries(root, regular_files(skill_root))
        except ValueError as exc:
            errors.append(str(exc))
            actual_subject = []
        expected_subject = admission.get("subject_files")
        if not isinstance(expected_subject, list):
            errors.append(f"ADMISSION_SUBJECT_FILES_INVALID:{name}")
            expected_subject = []
        errors.extend(
            compare_digest_entries(
                actual_subject, expected_subject, f"ADMISSION_SUBJECT:{name}"
            )
        )
        actual_tree_digest = tree_digest(actual_subject)
        if admission.get("skill_tree_sha256") != actual_tree_digest:
            errors.append(f"ADMISSION_TREE_DIGEST_DRIFT:{name}")

        expected_contracts = admission.get("contract_files")
        if not isinstance(expected_contracts, list) or not expected_contracts:
            errors.append(f"ADMISSION_CONTRACT_FILES_INVALID:{name}")
            expected_contracts = []
        actual_contracts: list[dict[str, str]] = []
        for entry in expected_contracts:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                errors.append(f"ADMISSION_CONTRACT_ENTRY_INVALID:{name}")
                continue
            try:
                path = safe_repo_path(root, entry["path"])
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not path.is_file():
                errors.append(f"ADMISSION_CONTRACT_ABSENT:{name}:{entry['path']}")
                continue
            actual_contracts.append(
                {"path": entry["path"], "sha256": sha256_file(path)}
            )
        errors.extend(
            compare_digest_entries(
                actual_contracts, expected_contracts, f"ADMISSION_CONTRACT:{name}"
            )
        )

        controls = admission.get("controls")
        if not isinstance(controls, list):
            errors.append(f"ADMISSION_CONTROLS_INVALID:{name}")
            controls = []
        control_map: dict[str, str] = {}
        for control in controls:
            if not isinstance(control, dict):
                errors.append(f"ADMISSION_CONTROL_NOT_OBJECT:{name}")
                continue
            control_id = control.get("id")
            state = control.get("state")
            if not isinstance(control_id, str) or not control_id:
                errors.append(f"ADMISSION_CONTROL_ID_INVALID:{name}")
                continue
            if control_id in control_map:
                errors.append(f"ADMISSION_CONTROL_DUPLICATE:{name}:{control_id}")
            control_map[control_id] = state
            if state != "PASS":
                errors.append(
                    f"ADMISSION_LOCAL_CONTROL_NOT_PASS:{name}:{control_id}:{state}"
                )
        for missing in sorted(MANDATORY_CONTROLS - set(control_map)):
            errors.append(f"ADMISSION_CONTROL_ABSENT:{name}:{missing}")
        # A row whose id is neither mandatory nor a case in this Skill's own
        # inventory has no producer at all -- it can only have been typed in.
        for unproduced in sorted(set(control_map) - produced_control_ids(skill_root)):
            errors.append(f"ADMISSION_CONTROL_UNPRODUCED:{name}:{unproduced}")

        ceiling = admission.get("evidence_ceiling")
        if ceiling not in EVIDENCE_LEVELS:
            errors.append(f"ADMISSION_EVIDENCE_CEILING_INVALID:{name}:{ceiling}")
        else:
            if EVIDENCE_LEVELS.index(ceiling) < minimum_index:
                errors.append(
                    f"ADMISSION_BELOW_MINIMUM:{name}:{ceiling}:{minimum}"
                )
            if row.get("evidence_ceiling") != ceiling:
                errors.append(f"REGISTRY_EVIDENCE_CEILING_DRIFT:{name}")

        not_claimed = admission.get("not_claimed")
        if not isinstance(not_claimed, list):
            errors.append(f"ADMISSION_NOT_CLAIMED_INVALID:{name}")
            not_claimed = []
        if ceiling in EVIDENCE_LEVELS:
            ceiling_index = EVIDENCE_LEVELS.index(ceiling)
            required_higher = {
                level
                for level in EVIDENCE_LEVELS[ceiling_index + 1 :]
                if level
                in {"L4_MATCHED_LIVE_RUNTIME", "L5_DELIVERY_AND_PRODUCTION"}
            }
            for level in sorted(required_higher - set(not_claimed)):
                errors.append(f"HIGHER_LAYER_NOT_EXPLICIT:{name}:{level}")

        if admission.get("authoring_command") not in authoring_commands(name):
            errors.append(f"AUTHORING_COMMAND_INVALID:{name}")
        if admission.get("hosted_evidence") not in {
            "READ_FROM_GITHUB",
            "NOT_EXERCISED",
        }:
            errors.append(f"HOSTED_EVIDENCE_INVALID:{name}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    return print_result("admissions", check(args.root.resolve()))


if __name__ == "__main__":
    raise SystemExit(main())
