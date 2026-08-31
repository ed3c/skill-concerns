#!/usr/bin/env python3
"""Deterministic validator for control-code-intel.

Fails closed unless the three layers are present and coherent: L0 portable
policy, L1 domain topology, L2 executable driver whose selftest passes; every
admitted tool has a receipt; LanceDB stays explicitly not-admitted with its
drop receipt. This is the hillclimb gate - edits may add capabilities and
receipts, never silently weaken the layer structure or admit an unbacked tool.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ADMITTED = {"grepai", "serena", "tree-sitter", "scip", "sqlite"}


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    def need(rel: str) -> Path | None:
        p = root / rel
        if not p.is_file():
            errors.append(f"missing L-layer file: {rel}")
            return None
        return p

    l0 = need("references/portable-code-intel-policy.md")
    l1 = need("domain/code-intel-topology.json")
    l2 = need("scripts/code_intel_driver.py")
    receipts_p = need("receipts.json")
    need("SKILL.md")
    need("references/procedures.md")

    if l0 and "L0 procedural" not in l0.read_text(encoding="utf-8"):
        errors.append("L0 policy does not declare itself the procedural layer")

    topo = {}
    if l1:
        topo = json.loads(l1.read_text(encoding="utf-8"))
        tools = set(topo.get("tools", {}))
        missing = ADMITTED - tools
        if missing:
            errors.append(f"L1 topology missing admitted tools: {sorted(missing)}")
        na = topo.get("not_admitted", {})
        if "lancedb" not in na:
            errors.append("L1 must record LanceDB as not_admitted with its drop receipt")
        elif not na["lancedb"].get("receipt"):
            errors.append("LanceDB not_admitted entry lacks a drop receipt")

    receipts = {}
    if receipts_p:
        receipts = json.loads(receipts_p.read_text(encoding="utf-8")).get("evidence", {})
        if not receipts:
            errors.append("receipts.json has no evidence")
        for key in ("cross-repo-verified", "pgvector-built-pg16", "connected-not-usable", "lancedb-dropped"):
            if key not in receipts:
                errors.append(f"receipts.json missing load-bearing receipt {key!r}")

    # L2 must be executable and its assertions must hold (including negatives).
    if l2:
        r = subprocess.run([sys.executable, str(l2), "--selftest"], capture_output=True, text=True)
        if r.returncode != 0:
            errors.append("L2 driver selftest failed (assertions or negative controls did not hold)")

    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1
    print("PASS: control-code-intel three-layer structure and receipts intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
