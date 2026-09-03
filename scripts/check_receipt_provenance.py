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

"Only make the gate red" also depends on read order, not just on which code
runs: the candidate subprocesses `run_checks` launches have full write access
to this same checked-out tree, `admission_path` included, for as long as they
run. `reproduce()` reads `admission_path` before calling `run_checks`, so a
candidate test that rewrites its own admission file at runtime is comparing
against bytes already captured -- it cannot launder that write into the
baseline it is being checked against.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from admission_stamp import StampRefused, build_receipt, declared_checks, run_checks
from common import REPO_ROOT, load_json, print_result, safe_repo_path


# The argv trace, ed3c/skill-concerns#81, LANDING TWO OF TWO
# (ed3c/skill-concerns#133).
#
# `build_receipt()` used to record which controls were measured and never which
# argv measured them: `bound` comes from `MANDATORY_PRODUCERS` plus the Skill's
# own `evals/cases.json`, never from `checks`. So a bundle graded through its
# permanent `run_all.SKILL_CHECKS` row and the same bundle graded through a
# `policy/bootstrap-admissions.json` entry produced byte-identical receipts, and
# the entry's argv -- reviewed once, on the trusted side -- left no trace in
# the artifact that review produced.
#
# The fix could not be one landing. This module runs from the DEFAULT BRANCH
# against the candidate (`verify.yml`), so a pull request that emits a new
# receipt field is graded by the old comparison, which demands the old bytes:
# planting exactly that change reds with
# `RECEIPT_NOT_REPRODUCED:control-backup:graded_by`. That is the tightening
# hazard `check_admissions.py`'s docstring names, from the other side.
#
# Landing one only WIDENED, with no data change, so this gate could accept the
# field before any receipt carried it. Landing two is the other half and CLOSES
# the transitional state rather than living in it: `build_receipt` emits the
# field, every receipt is regenerated through its own Skill's
# `gen_admission.py`, and the acceptance narrows back down -- an ABSENT field is
# a named diagnostic now, not the `return []` that tolerated it. Nothing is left
# optional, which is what stops `graded_by` from settling into the
# `unread-field` precedent (`skills/shadow-architect/domain/precedents.json` P1)
# permanently.
#
# `tests/test_receipt_provenance.py::GradedByTraceTests
# ::test_the_field_is_all_or_nothing_across_the_committed_set` is
# the reader that made the pair landable in this order: it requires the field to
# be all-or-nothing across the committed set. It passed before because the set
# was uniformly absent and passes now because the set is uniformly present, and
# a half-migrated set -- the state that would leave the widening permanent --
# reds it.
GRADED_BY = "graded_by"


def graded_by_errors(name: str, root: Path, committed: dict) -> list[str]:
    """Require a trace naming exactly the argv about to execute.

    Two named diagnostics rather than one byte mismatch, because the two states
    take different actions: ABSENT means a receipt produced by a stamper that
    predates the field and has to be regenerated through its Skill's own
    producer, MISMATCH means a receipt naming an execution that is not the one
    this gate selected. `RECEIPT_NOT_REPRODUCED:<skill>:graded_by` would
    collapse both into "the bytes differ", which is true and unactionable.
    """
    if GRADED_BY not in committed:
        return [f"RECEIPT_GRADED_BY_ABSENT:{name}"]
    try:
        executed = [list(argv) for argv in declared_checks(name, root)]
    except StampRefused as exc:
        return [str(exc)]
    if committed[GRADED_BY] != executed:
        return [f"RECEIPT_GRADED_BY_MISMATCH:{name}"]
    return []


def reproduce(root: Path, name: str, admission_path: Path) -> list[str]:
    """Re-run `name`'s checks and compare the receipt they imply to the bytes.

    `actual` is read *before* `run_checks` executes anything. `run_checks`
    launches the candidate's own subject scripts and test modules as
    subprocesses with `cwd=root` -- full write access to this same tree,
    `admission_path` included. Reading the comparison baseline after that
    execution would let a candidate test's own runtime writes become the
    thing this function compares against, making the check agree with
    whatever the candidate just wrote rather than with what was committed.
    """
    actual = admission_path.read_text(encoding="utf-8")
    try:
        committed = json.loads(actual)
    except json.JSONDecodeError:
        return [f"RECEIPT_NOT_REPRODUCED:{name}:UNPARSEABLE"]
    try:
        bound = run_checks(name, root)
    except StampRefused as exc:
        return [str(exc)]
    produced = build_receipt(name, root, bound)
    # One owner for one field, and NOT an exemption from the reproduction: the
    # field is popped from both sides here only so it is not reported twice, and
    # `graded_by_errors` holds it against the selection that just executed --
    # value for value, ABSENT and MISMATCH named separately because they take
    # different actions. Nothing about `graded_by` is accepted that the byte
    # comparison would have refused; the comparison just says less about it.
    # Popping and re-serialising rather than diffing key by key keeps the rest
    # byte-exact: `build_receipt` writes with the same `indent=2` and the same
    # key order, so the remainder is the same bytes it would have produced.
    produced.pop(GRADED_BY)
    expected = json.dumps(produced, indent=2) + "\n"

    errors: list[str] = []
    if isinstance(committed, dict):
        errors.extend(graded_by_errors(name, root, committed))
        committed.pop(GRADED_BY, None)
        actual = json.dumps(committed, indent=2) + "\n"
    if actual == expected:
        return errors
    # Name the field that differs; a bare byte mismatch is unactionable.
    drifted = sorted(
        key
        for key in set(produced) | set(committed)
        if produced.get(key) != committed.get(key)
    )
    errors.extend(f"RECEIPT_NOT_REPRODUCED:{name}:{key}" for key in drifted)
    if not drifted:
        errors.append(f"RECEIPT_NOT_REPRODUCED:{name}:FORMATTING")
    return errors


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
