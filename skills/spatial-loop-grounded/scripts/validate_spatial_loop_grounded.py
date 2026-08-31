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
        if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and REF_RE.fullmatch(r) for r in refs):
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
