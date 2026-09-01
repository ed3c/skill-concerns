#!/usr/bin/env python3
"""Deterministic validator for context-closure-engineering.

Fails closed unless the three layers are present and tied to each other: L0
portable laws, L1 domain topology, L2 executable checker whose selftest passes.

The tie is a count plus an id set, not a cross-reference: L1 declares how many
portable laws and how many planted negatives exist, and this gate refuses when
the L0 clause headings or the topology rows disagree with those numbers.
Dropping a law or quietly demoting a mechanized negative to prose therefore
reds here instead of shrinking the contract behind a still-green suite. Every
negative declared MECHANIZED must name checks that exist in the L2 checker's
bytes; every NOT_MECHANIZED one must name an owner and a reason.

A count alone is self-referential: a topology.json edit that removes one row
and decrements its count field in the same edit leaves `count == len(rows)`
true throughout, so that tie alone cannot see it. Each id set below is also
checked against a copy hard-coded in this file's own bytes, not read from the
topology, so the same-file edit that fools the count still reds against a
set the edit never touched.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

LAW_HEADING = re.compile(r"^## (LAW-[A-Z-]+)\s*$", re.MULTILINE)

# Independent-of-JSON ground truth: hard-coded here so that editing the L1
# topology's row list and its own count field together -- which a purely
# self-referential `count == len(rows)` tie cannot see, since both numbers
# move together -- still reds against a set this file does not share bytes
# with. Precedent: skills/control-backup/scripts/validate_control_backup.py
# hard-codes its ADMITTED provider set the same way.
EXPECTED_LAW_IDS = {
    "LAW-DENOMINATOR", "LAW-ANCHOR", "LAW-NO-PROMOTION", "LAW-EDGE-SPLIT",
    "LAW-ONE-CONVERGENCE-OWNER", "LAW-TRACE-GAP", "LAW-NO-MUTATION",
    "LAW-EXTERNAL-CLAIM",
}
EXPECTED_NEGATIVE_IDS = {"PN-1", "PN-2", "PN-3", "PN-4", "PN-5", "PN-6", "PN-7"}


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    def need(rel: str) -> Path | None:
        p = root / rel
        if not p.is_file():
            errors.append(f"missing L-layer file: {rel}")
            return None
        return p

    l0 = need("references/portable-context-closure-policy.md")
    l1 = need("domain/context-closure-topology.json")
    l2 = need("scripts/check_context_pack.py")
    need("SKILL.md")
    need("references/consumer-adapter-contract.md")
    need("evals/fixtures/baseline.json")

    l0_text = l0.read_text(encoding="utf-8") if l0 else ""
    if l0 and "L0 procedural" not in l0_text:
        errors.append("L0 policy does not declare itself the procedural layer")

    topology = json.loads(l1.read_text(encoding="utf-8")) if l1 else {}
    l2_text = l2.read_text(encoding="utf-8") if l2 else ""

    # L0 <-> L1: the law set is closed on both the count and the ids.
    laws = topology.get("portable_laws", [])
    declared_count = topology.get("portable_law_count")
    if declared_count != len(laws):
        errors.append(
            f"L1 portable_law_count {declared_count} != {len(laws)} declared rows"
        )
    clause_ids = set(LAW_HEADING.findall(l0_text))
    law_ids = {law.get("id") for law in laws}
    if clause_ids != law_ids:
        errors.append(
            f"L0 clause headings {sorted(clause_ids)} != L1 law ids {sorted(law_ids)}"
        )
    if declared_count != len(clause_ids):
        errors.append(
            f"L0 carries {len(clause_ids)} law clauses, L1 declares {declared_count}"
        )
    if law_ids != EXPECTED_LAW_IDS:
        errors.append(
            f"L1 law ids {sorted(law_ids)} != hard-coded expected {sorted(EXPECTED_LAW_IDS)}"
        )

    # L1 <-> L2: a mechanized negative names checks the checker actually emits;
    # an unmechanized one names who owns it and why it stays open.
    negatives = topology.get("planted_negatives", [])
    if topology.get("planted_negative_count") != len(negatives):
        errors.append(
            f"L1 planted_negative_count {topology.get('planted_negative_count')} "
            f"!= {len(negatives)} declared rows"
        )
    negative_ids = {negative.get("id") for negative in negatives}
    if negative_ids != EXPECTED_NEGATIVE_IDS:
        errors.append(
            f"L1 planted_negative ids {sorted(negative_ids)} != hard-coded "
            f"expected {sorted(EXPECTED_NEGATIVE_IDS)}"
        )
    for negative in negatives:
        identifier = negative.get("id")
        if negative.get("state") == "MECHANIZED":
            checks = negative.get("checks") or []
            if not checks:
                errors.append(f"{identifier} is MECHANIZED with no checks")
            for code in checks:
                if code not in l2_text:
                    errors.append(f"{identifier} names check {code!r} absent from L2")
        elif negative.get("state") == "NOT_MECHANIZED":
            for field in ("owner", "reason"):
                if not negative.get(field):
                    errors.append(f"{identifier} is NOT_MECHANIZED without {field}")
        else:
            errors.append(f"{identifier} has unknown state {negative.get('state')!r}")

    # The consumer canary must stay explicit and may not be claimed from here.
    canary = topology.get("consumer_canary", {})
    if canary.get("state") not in {"NOT_EXERCISED", "BLOCKED"}:
        errors.append(
            f"consumer_canary state {canary.get('state')!r} claims more than this "
            "hermetic bundle can prove"
        )

    # L2 must execute: positive control on the fixture, then every mechanized
    # negative must go red.
    if l2:
        for argv in (
            [sys.executable, str(l2), "--selftest"],
            [sys.executable, str(l2), "--pack", str(root / "evals" / "fixtures" / "pack"),
             "--baseline", str(root / "evals" / "fixtures" / "baseline.json")],
        ):
            if subprocess.run(argv, capture_output=True, text=True).returncode != 0:
                errors.append(f"L2 checker failed: {' '.join(argv[1:])}")

    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: context-closure-engineering three layers are present and count-tied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
