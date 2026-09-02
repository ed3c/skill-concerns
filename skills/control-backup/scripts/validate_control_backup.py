#!/usr/bin/env python3
"""Deterministic validator for control-backup.

Fails closed unless the three layers are present and coherent: L0 portable
policy, L1 domain topology, L2 executable driver whose selftest passes; every
admitted tool has a receipt; openrsync stays explicitly not-admitted with its
hot-source drop receipt. This is the hillclimb gate - edits may add tiers and
receipts, never silently weaken the layer structure or admit an unbacked tool.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Count tie to this Skill's own entrypoint (ed3c/skill-concerns#74): the exact
# `## ` section headings of SKILL.md. `scripts/check_skill_bundles.py` reads
# this tuple out of these bytes -- parsed, never imported -- and reds when the
# entrypoint's headings differ, so a hollowed SKILL.md cannot pass behind a
# still-green validator. Editing SKILL.md's section structure is meant to force
# an edit here; that is the tie, not an inconvenience.
SKILL_MD_CLAUSES = (
    "Decision boundary",
    "Hard constraints",
    "Knowledge placement",
)

ADMITTED = {"gnu-rsync", "link-dest", "launchd", "mcp-drive-text"}
LOAD_BEARING_RECEIPTS = (
    "openrsync-hot-source-fatal",
    "gnu-rsync-exit24",
    "freeze-then-replicate-verified",
    "linkdest-inode-verified",
    "same-second-quickcheck-hazard",
    "exfat-no-hardlink",
    "rotation-floor-unattainable-bug",
    "single-writer-race",
    "exclude-protects-leftovers",
)


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    def need(rel: str) -> Path | None:
        p = root / rel
        if not p.is_file():
            errors.append(f"missing L-layer file: {rel}")
            return None
        return p

    l0 = need("references/portable-backup-policy.md")
    l1 = need("domain/backup-topology.json")
    l2 = need("scripts/backup_driver.py")
    receipts_p = need("receipts.json")
    producer = need("scripts/gen_backup_receipts.py")
    need("SKILL.md")
    need("references/procedures.md")

    if l0 and "L0 procedural" not in l0.read_text(encoding="utf-8"):
        errors.append("L0 policy does not declare itself the procedural layer")

    if l1:
        topo = json.loads(l1.read_text(encoding="utf-8"))
        tools = set(topo.get("tools", {}))
        missing = ADMITTED - tools
        if missing:
            errors.append(f"L1 topology missing admitted tools: {sorted(missing)}")
        na = topo.get("not_admitted", {})
        if "openrsync" not in na:
            errors.append("L1 must record openrsync as not_admitted with its hot-source receipt")
        elif not na["openrsync"].get("receipt"):
            errors.append("openrsync not_admitted entry lacks a receipt")

    if receipts_p:
        receipts = json.loads(receipts_p.read_text(encoding="utf-8")).get("evidence", {})
        if not receipts:
            errors.append("receipts.json has no evidence")
        for key in LOAD_BEARING_RECEIPTS:
            if key not in receipts:
                errors.append(f"receipts.json missing load-bearing receipt {key!r}")

    # L2 must be executable and its assertions must hold (including negatives).
    selftest = None
    if l2:
        selftest = subprocess.run(
            [sys.executable, str(l2), "--selftest"], capture_output=True, text=True
        )
        if selftest.returncode != 0:
            errors.append("L2 driver selftest failed (assertions or negative controls did not hold)")

    # ed3c/skill-concerns#84: the `producer` fields have one author, and it is
    # an execution. Re-derive them here so a hand edit of what the producer owns
    # reds - the generator refuses any key whose assertion is absent or went
    # red, so a green check means the driver just replayed every claim it
    # stamps. The selftest bytes are piped in rather than the driver being run a
    # second time: the receipt is then checked against THE execution this
    # validator graded, not against a different one that happened to agree.
    if producer and selftest is not None:
        checked = subprocess.run(
            [sys.executable, str(producer), "--check", "--from-stdin"],
            input=selftest.stdout,
            capture_output=True,
            text=True,
        )
        if checked.returncode != 0:
            errors.append(checked.stdout.strip() or "gen_backup_receipts.py --check refused")

    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print("PASS: control-backup three-layer structure and receipts intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
