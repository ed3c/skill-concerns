#!/usr/bin/env python3
"""receipts.json's only author: a projection of the precedent ledger.

Each precedent already carries the monitor record that wrote the finding down
and the provider receipts that ground it. Copying those into a second file by
hand is the laundering this repository's supervision clauses forbid, so this
producer derives them and `validate_shadow_architect.py` re-derives and
compares. A hand edit reds, even when the edit would be factually right.

Putting the provider refs here is also how this bundle rides the cadence that
already exists: the repository's freshness sweep globs `skills/*/receipts.json`
and re-resolves every provider ref it finds. No new scheduler.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PROVIDER_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$")
PRODUCER = "python3 skills/shadow-architect/scripts/gen_shadow_receipts.py"


class ReceiptRefused(RuntimeError):
    """Raised instead of writing an evidence entry nothing can re-resolve."""


def build(ledger: dict) -> dict:
    evidence: dict[str, dict] = {}
    for precedent in ledger.get("precedents") or []:
        clause = precedent.get("id")
        provenance = precedent.get("provenance") or {}
        refs = sorted(
            {
                ref
                for ref in provenance.get("wave_receipt") or []
                if isinstance(ref, str) and PROVIDER_REF.fullmatch(ref)
            }
        )
        if not refs:
            raise ReceiptRefused(
                f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: the clause names no provider "
                "receipt, so the cadence sweep has nothing to re-resolve"
            )
        if not str(provenance.get("quote") or "").strip():
            raise ReceiptRefused(
                f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: no monitor quote, so nothing "
                "says what the wave actually found"
            )
        evidence[clause] = {
            "refs": refs,
            "claim": provenance["quote"],
            "wave": provenance.get("wave"),
            "monitor_record": provenance.get("monitor_record"),
            "subject_commit": provenance.get("subject_commit"),
        }
    return {
        "schema_version": 1,
        "producer": PRODUCER,
        "note": (
            "Derived from domain/precedents.json. Hand edits are refused: "
            "validate_shadow_architect.py re-derives these bytes and compares."
        ),
        "evidence": evidence,
    }


def render(ledger: dict) -> str:
    return json.dumps(build(ledger), indent=2) + "\n"


def main() -> int:
    ledger = json.loads(
        (SKILL_ROOT / "domain" / "precedents.json").read_text(encoding="utf-8")
    )
    out = SKILL_ROOT / "receipts.json"
    out.write_text(render(ledger), encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
