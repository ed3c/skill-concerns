#!/usr/bin/env python3
"""receipts.json's only author: it is a projection of the topology, never a document.

The evidence table is derived, not written: each entry's refs are the provider
and host refs carried by the topology rows bound to that evidence id, and the
claim is the topology's own claim text. `validate_arrival_engineering.py`
re-derives these bytes and compares, so a hand edit reds -- the C5 discipline
with a mechanical reader instead of a sentence.

Putting the refs here is also what makes SHADOW ride the existing cadence:
`scripts/maintain_skills.py` globs `skills/*/receipts.json` and re-resolves
every provider ref it finds, so this bundle's cross-repo pointers get
re-verified by a sweep that already runs. No new scheduler.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PROVIDER_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$")
HOST_REF = re.compile(r"^host:\S+$")
PRODUCER = "python3 skills/arrival-engineering/scripts/gen_receipts.py"


class ReceiptRefused(RuntimeError):
    """Raised instead of writing an evidence entry nothing can re-resolve."""


def build(topology: dict) -> dict:
    claims = topology.get("evidence_claims") or {}
    rows = topology.get("rows") or []
    evidence: dict[str, dict] = {}
    for evidence_id, claim in sorted(claims.items()):
        bound = [row for row in rows if row.get("evidence") == evidence_id]
        if not bound:
            raise ReceiptRefused(f"EVIDENCE_WITHOUT_ROW:{evidence_id}")
        refs = sorted(
            {
                receipt["ref"]
                for row in bound
                for receipt in row.get("receipts") or []
                if isinstance(receipt, dict)
                and isinstance(receipt.get("ref"), str)
                and (PROVIDER_REF.fullmatch(receipt["ref"]) or HOST_REF.fullmatch(receipt["ref"]))
            }
        )
        if not refs:
            raise ReceiptRefused(
                f"EVIDENCE_WITHOUT_RESOLVABLE_REF:{evidence_id}: no bound row carries a "
                "provider or host ref, so the cadence sweep has nothing to re-resolve"
            )
        evidence[evidence_id] = {
            "refs": refs,
            "claim": claim,
            "rows": sorted(row["id"] for row in bound),
        }
    return {
        "schema_version": 1,
        "producer": PRODUCER,
        "note": (
            "Derived from domain/capability-topology.json. Hand edits are refused: "
            "validate_arrival_engineering.py re-derives these bytes and compares."
        ),
        "evidence": evidence,
    }


def render(topology: dict) -> str:
    return json.dumps(build(topology), indent=2) + "\n"


def main() -> int:
    topology = json.loads(
        (SKILL_ROOT / "domain" / "capability-topology.json").read_text(encoding="utf-8")
    )
    out = SKILL_ROOT / "receipts.json"
    out.write_text(render(topology), encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
