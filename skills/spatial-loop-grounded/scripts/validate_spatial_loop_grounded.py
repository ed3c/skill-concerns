#!/usr/bin/env python3
"""Deterministic validator for the spatial-loop-grounded skill.

Fails closed when any clause loses its trigger form or its receipt binding:
this is the hillclimb gate - edits may add evidence and clauses, never
silently weaken them.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CLAUSE_RE = re.compile(r"^## (C\d+)\. ", re.M)
REQUIRED_FIELDS = ("- Signal:", "- Action:", "- Why:", "- evidence:")
REF_RE = re.compile(r"^ed3c/[a-z-]+#\d+$")
# host-environment receipts (non-repository evidence) name their exact host artifact
HOST_REF_RE = re.compile(r"^host:\S+$")
KERNEL_RE = re.compile(r"^- (K\d+) ", re.M)


def _ref_ok(ref: object) -> bool:
    return isinstance(ref, str) and bool(REF_RE.fullmatch(ref) or HOST_REF_RE.fullmatch(ref))


def validate(skill_root: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_root / "SKILL.md"
    receipts_path = skill_root / "receipts.json"
    if not skill_md.is_file():
        return ["SKILL.md missing"]
    if not receipts_path.is_file():
        return ["receipts.json missing"]
    text = skill_md.read_text(encoding="utf-8")
    receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
    evidence = receipts.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        errors.append("receipts.json evidence table missing or empty")
        evidence = {}
    for key, entry in evidence.items():
        refs = entry.get("refs") if isinstance(entry, dict) else None
        if not isinstance(refs, list) or not refs or not all(_ref_ok(r) for r in refs):
            errors.append(f"receipts.json evidence {key!r} has no valid provider refs")
        if not isinstance(entry, dict) or not str(entry.get("claim") or "").strip():
            errors.append(f"receipts.json evidence {key!r} has no claim")

    clause_ids = CLAUSE_RE.findall(text)
    if len(clause_ids) < 8:
        errors.append(f"expected at least 8 clauses, found {len(clause_ids)}")
    if len(clause_ids) != len(set(clause_ids)):
        errors.append("duplicate clause ids")

    sections = CLAUSE_RE.split(text)
    used_evidence: set[str] = set()
    for index in range(1, len(sections), 2):
        clause_id = sections[index]
        body = sections[index + 1]
        body = body.split("\n## ", 1)[0]
        for field in REQUIRED_FIELDS:
            if field not in body:
                errors.append(f"{clause_id}: trigger form incomplete, missing {field!r}")
        match = re.search(r"^- evidence: (.+)$", body, re.M)
        if match:
            for token in (item.strip() for item in match.group(1).split(",")):
                used_evidence.add(token)
                if token not in evidence:
                    errors.append(f"{clause_id}: evidence id {token!r} not in receipts.json")

    for key in evidence:
        if key not in used_evidence:
            errors.append(f"receipts.json evidence {key!r} is bound to no clause")

    if "Non-claims" not in text:
        errors.append("Non-claims section missing")
    if "skills-shared" not in text:
        errors.append("upstream provenance pointer missing")

    # L0 kernel: one domain-free kernel per clause, counts tied.
    kernel_path = skill_root / "references" / "portable-supervision-kernel.md"
    if not kernel_path.is_file():
        errors.append("L0 kernel references/portable-supervision-kernel.md missing")
    else:
        kernel_text = kernel_path.read_text(encoding="utf-8")
        if "L0 procedural" not in kernel_text:
            errors.append("L0 kernel does not declare itself the procedural layer")
        kernels = KERNEL_RE.findall(kernel_text)
        if len(kernels) != len(clause_ids):
            errors.append(
                f"kernel/clause count mismatch: {len(kernels)} kernels vs {len(clause_ids)} clauses"
            )

    # L1 topology: every primitive self-defined and receipt-bound.
    topology_path = skill_root / "domain" / "machine-topology.json"
    if not topology_path.is_file():
        errors.append("L1 domain/machine-topology.json missing")
    else:
        topology = json.loads(topology_path.read_text(encoding="utf-8"))
        primitives = topology.get("primitives")
        if not isinstance(primitives, dict) or not primitives:
            errors.append("topology primitives missing or empty")
        else:
            for name, prim in primitives.items():
                if not isinstance(prim, dict) or not str(prim.get("what") or "").strip() or not str(prim.get("owner") or "").strip():
                    errors.append(f"topology primitive {name!r} lacks what/owner")
                    continue
                prim_evidence = prim.get("evidence")
                if not isinstance(prim_evidence, list) or not prim_evidence:
                    errors.append(f"topology primitive {name!r} carries no evidence ids")
                    continue
                for token in prim_evidence:
                    if token not in evidence:
                        errors.append(f"topology primitive {name!r}: evidence id {token!r} not in receipts.json")
    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: spatial-loop-grounded clause and receipt bindings intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
