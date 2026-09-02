#!/usr/bin/env python3
"""receipts.json's only author: a projection of the catalogue, never a document.

Each catalogue class already carries the receipt that grounded it and the wave
whose ledger entry recorded it; copying those into a second file by hand is the
laundering `spatial-loop-grounded` C5 forbids, so this producer derives them and
`validate_red_team.py` re-derives and compares. A hand edit reds.

Putting the provider refs here is also how this bundle rides the existing
cadence: `scripts/maintain_skills.py` globs `skills/*/receipts.json` and
re-resolves every provider ref it finds. No new scheduler.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PROVIDER_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$")
PRODUCER = "python3 skills/red-team/scripts/gen_red_team_receipts.py"


class ReceiptRefused(RuntimeError):
    """Raised instead of writing an evidence entry nothing can re-resolve."""


def build(catalogue: dict) -> dict:
    evidence: dict[str, dict] = {}
    for entry in catalogue.get("classes") or []:
        class_id = entry.get("id")
        provenance = entry.get("provenance") or {}
        refs = [
            ref
            for ref in provenance.get("receipts") or []
            if isinstance(ref, str) and PROVIDER_REF.fullmatch(ref)
        ]
        if not refs:
            raise ReceiptRefused(
                f"EVIDENCE_WITHOUT_RESOLVABLE_REF:{class_id}: the class names no provider "
                "ref, so the cadence sweep has nothing to re-resolve"
            )
        evidence[class_id] = {
            "refs": sorted(refs),
            "claim": provenance.get("why", ""),
            "ledger": provenance.get("ledger", ""),
            "status": entry.get("status"),
        }
    for claim_id, claim in sorted((catalogue.get("method_claims") or {}).items()):
        refs = [
            ref
            for ref in claim.get("refs") or []
            if isinstance(ref, str) and PROVIDER_REF.fullmatch(ref)
        ]
        if not refs:
            raise ReceiptRefused(f"EVIDENCE_WITHOUT_RESOLVABLE_REF:{claim_id}")
        # `authorization` rides into the evidence table on purpose. Without it a
        # method claim sits beside a measured class looking identically grounded,
        # and this table's whole job is that grounding is a readback.
        evidence[claim_id] = {
            "refs": sorted(refs),
            "claim": claim.get("claim", ""),
            "authorization": claim.get("authorization"),
        }
    return {
        "schema_version": 1,
        "producer": PRODUCER,
        "note": (
            "Derived from domain/catalogue.json. Hand edits are refused: "
            "validate_red_team.py re-derives these bytes and compares."
        ),
        "evidence": evidence,
    }


def render(catalogue: dict) -> str:
    return json.dumps(build(catalogue), indent=2) + "\n"


def main() -> int:
    catalogue = json.loads(
        (SKILL_ROOT / "domain" / "catalogue.json").read_text(encoding="utf-8")
    )
    out = SKILL_ROOT / "receipts.json"
    out.write_text(render(catalogue), encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
