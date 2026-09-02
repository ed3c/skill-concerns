#!/usr/bin/env python3
"""receipts.json's `producer` field has one author, and it is an execution.

Before this, the nine driver-producer fields in `../receipts.json` were set by a
one-off scratch script that walked a hand-authored table and did an anchor-unique
text insert. The mapping had been verified one-by-one against `backup_driver`'s
selftest call sites, so the bytes were factually right - and still the wrong
shape: hand-editing evidence is laundering even when the edit would be right
(`spatial-loop-grounded` C5, ed3c/skill-concerns#84).

`control-noodle`'s `gen_procedure_pin.py` could be a pure read-and-copy because
its source of truth already names the destination fields verbatim. This one
cannot: the driver asserts on `Assertion.name` strings (`vanish_exit_tolerated`)
that do not match the receipt scenario keys (`gnu-rsync-exit24`). Issue #84
admits either renaming the driver's assertions or authoring a correspondence
table here; the table is chosen, because renaming reaches into tested,
currently-green driver code to move a name that is already correct for its own
reader.

What the table is and is not:

- it is the claim "this receipt is replayed by exactly these assertions", and a
  `producer` field is written only when every one of them JUST PASSED in a real
  `--selftest` run of this Skill's own driver;
- it is refused, never guessed: a receipt naming an assertion that does not
  exist, an assertion that went red, or an entry claiming this driver with no
  correspondence at all, aborts the whole write;
- it is NOT a claim that every receipt has a producer. `HOST_OBSERVED` and
  provider `refs` are untouched here, which is what keeps the typed exit an
  earned default rather than an escape hatch this generator could type for you.

Declared ceiling: `--check` compares the committed bytes to what this producer
emits from the same document, so it catches drift in what it DERIVES - the
`producer` fields and the emitted shape - and nothing else. The hand-authored
`claim` and `how` prose is not derivable from any execution, is not checked
here, and stays a reviewer's read. Saying otherwise would be the same
overclaim in the instrument that the instrument exists to catch.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
DRIVER = "scripts/backup_driver.py"
RECEIPTS = "receipts.json"

# `[PASS] <name>: <detail>` / `[FAIL] <name>: <detail>`. Non-greedy up to the
# first ": " because negative-control names carry an unspaced colon of their own
# (`negative_control:absent volume`), which this must not split on.
ASSERTION_LINE = re.compile(r"^\[(PASS|FAIL)\] (.*?): ")

# receipt key -> every assertion whose green is what grounds it. Verified
# one-by-one against selftest() call sites in scripts/backup_driver.py; where a
# receipt records a hazard, the negative control that reproduces it is named
# alongside the positive, because a rule proven in one direction only is half a
# ground.
CORRESPONDENCE: dict[str, tuple[str, ...]] = {
    "openrsync-hot-source-fatal": (
        "vanish_exit_tolerated",
        "negative_control:real transfer error is fatal",
    ),
    "gnu-rsync-exit24": ("vanish_exit_tolerated",),
    "freeze-then-replicate-verified": (
        "replicate_source_frozen",
        "negative_control:slow tier on live sources",
    ),
    "linkdest-inode-verified": (
        "linkdest_dedups_unchanged",
        "linkdest_isolates_changed",
        "linkdest_preserves_history",
    ),
    "same-second-quickcheck-hazard": ("same_second_hazard_reproduces",),
    "rotation-floor-unattainable-bug": (
        "rotation_attainable",
        "negative_control:the shipped unattainable floor (keep 2 + 5G) is caught",
    ),
    "single-writer-race": (
        "lock_takeover",
        "negative_control:live holder is never robbed",
    ),
    "exclude-protects-leftovers": ("exclude_protects_leftover",),
    "mount-point-guard": (
        "dest_is_mountpoint",
        "negative_control:absent volume",
    ),
}


class ReceiptRefused(RuntimeError):
    """Raised instead of stamping a producer no execution earned."""


def parse_assertions(output: str) -> dict[str, bool]:
    """{assertion name: passed} from a driver selftest's own stdout.

    A name asserted more than once (the driver checks the tolerated exit class
    twice) is the conjunction: one green occurrence must not cover a red one.
    """
    results: dict[str, bool] = {}
    for line in output.splitlines():
        match = ASSERTION_LINE.match(line)
        if not match:
            continue
        passed = match.group(1) == "PASS"
        name = match.group(2)
        results[name] = results.get(name, True) and passed
    if not results:
        raise ReceiptRefused(
            f"DRIVER_PRODUCED_NO_ASSERTIONS:{DRIVER}: nothing was replayed, so "
            "nothing is grounded"
        )
    return results


def run_driver(skill_root: Path = SKILL_ROOT) -> dict[str, bool]:
    """Run this Skill's driver selftest and read the assertions off it."""
    result = subprocess.run(
        [sys.executable, str(skill_root / DRIVER), "--selftest"],
        capture_output=True,
        text=True,
    )
    return parse_assertions(result.stdout)


def build(document: dict, results: dict[str, bool]) -> dict:
    """Stamp `producer` for every positively matched key; refuse otherwise."""
    stamped = copy.deepcopy(document)
    evidence = stamped.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        raise ReceiptRefused("RECEIPT_EVIDENCE_EMPTY: nothing to ground")
    for key in CORRESPONDENCE:
        if key not in evidence:
            raise ReceiptRefused(
                f"CORRESPONDENCE_KEY_ABSENT:{key}: the table names a receipt this "
                "file no longer carries, so the table is stale"
            )
    for key, entry in evidence.items():
        assertions = CORRESPONDENCE.get(key)
        if assertions is None:
            if entry.get("producer") == DRIVER:
                raise ReceiptRefused(
                    f"RECEIPT_PRODUCER_UNEARNED:{key}: claims {DRIVER} with no "
                    "correspondence, so no assertion was ever named for it"
                )
            continue
        missing = [name for name in assertions if name not in results]
        if missing:
            raise ReceiptRefused(
                f"RECEIPT_ASSERTION_ABSENT:{key}:{','.join(missing)}: the driver "
                "asserts nothing by that name"
            )
        red = [name for name in assertions if not results[name]]
        if red:
            raise ReceiptRefused(
                f"RECEIPT_ASSERTION_RED:{key}:{','.join(red)}: the assertion that "
                "would ground this receipt did not hold"
            )
        entry["producer"] = DRIVER
    return stamped


def render(document: dict, results: dict[str, bool]) -> str:
    return json.dumps(build(document, results), indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the committed bytes to what this producer makes; write nothing",
    )
    parser.add_argument(
        "--from-stdin",
        action="store_true",
        help=(
            "read the driver selftest's stdout from stdin instead of running it "
            "again, so a caller that just ran the driver checks against THAT "
            "execution rather than a second one"
        ),
    )
    args = parser.parse_args(argv)
    path = SKILL_ROOT / RECEIPTS
    document = json.loads(path.read_text(encoding="utf-8"))
    try:
        results = parse_assertions(sys.stdin.read()) if args.from_stdin else run_driver()
        produced = render(document, results)
    except ReceiptRefused as exc:
        print(f"REFUSED: {exc}")
        return 1
    if args.check:
        if path.read_text(encoding="utf-8") != produced:
            print(
                f"REFUSED: RECEIPT_NOT_PRODUCED:{RECEIPTS} is not what "
                f"{Path(__file__).name} produces - a `producer` field or the emitted "
                "shape was written by something other than this producer; regenerate "
                "it. Hand-editing what a producer owns is laundering even when the "
                "edit would be factually right"
            )
            return 1
        print(f"check OK: {RECEIPTS} is exactly what its producer makes")
        return 0
    path.write_text(produced, encoding="utf-8")
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
