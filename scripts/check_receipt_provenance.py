#!/usr/bin/env python3
"""Require every committed receipt to be reproducible by re-running its checks.

`check_admissions.py` verifies a receipt is internally consistent: digests match
the tree that is there, every mandatory id is present, every row says `PASS`.
None of that requires the checks to have run. A receipt with correct digests and
`"state": "PASS"` on every row passes it whether `admission_stamp.stamp()` wrote
it or a person typed it -- `admissions/control-noodle.json` was in fact committed
hand-authored once. The stamper's refusal closed the honest path only; CI's
trusted step never executed `SKILL_CHECKS` itself, and the job that does
(`candidate-self-tests`) runs the candidate's own unaudited `run_all.py`.

This gate closes the dishonest path by making the receipt a *function* of an
execution rather than a document about one: it re-runs the Skill's declared
checks and every control's producer against the candidate tree, rebuilds the
receipt, and requires the committed bytes to be exactly that. There is nothing
left to hand-author -- a forged row would have to be a row the re-execution also
produces, which means the execution happened.

Trust boundary, matching `verify.yml`'s "the candidate is only ever data": the
declaration of what to run (`run_all.SKILL_CHECKS`), the producer table, the
receipt shape and the comparison all come from *this* file's tree, which in CI
is the default branch checkout. Only the subject scripts under `skills/` execute
from the candidate, which is unavoidable -- they are what is being admitted --
and they can only make the gate red, never green: a candidate `run_all.py` or
`admission_stamp.py` is never imported or executed here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from admission_stamp import StampRefused, build_receipt, run_checks
from common import REPO_ROOT, load_json, print_result, safe_repo_path


def reproduce(root: Path, name: str, admission_path: Path) -> list[str]:
    """Re-run `name`'s checks and compare the receipt they imply to the bytes."""
    try:
        bound = run_checks(name, root)
    except StampRefused as exc:
        return [str(exc)]
    expected = json.dumps(build_receipt(name, root, bound), indent=2) + "\n"
    actual = admission_path.read_text(encoding="utf-8")
    if actual == expected:
        return []
    # Name the field that differs; a bare byte mismatch is unactionable.
    try:
        committed = json.loads(actual)
    except json.JSONDecodeError:
        return [f"RECEIPT_NOT_REPRODUCED:{name}:UNPARSEABLE"]
    produced = json.loads(expected)
    drifted = sorted(
        key
        for key in set(produced) | set(committed)
        if produced.get(key) != committed.get(key)
    )
    return [f"RECEIPT_NOT_REPRODUCED:{name}:{key}" for key in drifted] or [
        f"RECEIPT_NOT_REPRODUCED:{name}:FORMATTING"
    ]


def check(root: Path = REPO_ROOT, only: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_json(root / "registry.json")
    except ValueError as exc:
        return [str(exc)]
    rows = registry.get("skills") if isinstance(registry, dict) else None
    if not isinstance(rows, list):
        return ["REGISTRY_SKILLS_NOT_LIST"]

    for row in rows:
        if not isinstance(row, dict):
            errors.append("REGISTRY_SKILL_ROW_NOT_OBJECT")
            continue
        name = row.get("name")
        if only is not None and name not in only:
            continue
        admission = row.get("admission")
        if not isinstance(name, str) or not isinstance(admission, str):
            errors.append(f"REGISTRY_ADMISSION_PATH_INVALID:{name}")
            continue
        try:
            admission_path = safe_repo_path(root, admission)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not admission_path.is_file():
            errors.append(f"ADMISSION_RECEIPT_ABSENT:{name}")
            continue
        errors.extend(reproduce(root, name, admission_path))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--skill", action="append", help="reproduce only this Skill (repeatable)"
    )
    args = parser.parse_args(argv)
    only = set(args.skill) if args.skill else None
    return print_result(
        "receipt-provenance", check(args.root.resolve(), only)
    )


if __name__ == "__main__":
    raise SystemExit(main())
