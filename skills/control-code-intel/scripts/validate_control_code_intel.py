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

# Count tie to this Skill's own entrypoint (ed3c/skill-concerns#74): the exact
# `## ` section headings of SKILL.md, read out of these bytes by
# `scripts/check_skill_bundles.py` so a hollowed SKILL.md reds against a tuple
# the hollowing never touched.
SKILL_MD_CLAUSES = (
    "Decision boundary",
    "Backends and their boundary",
    "Best-path procedures",
    "Environment contract",
    "Hard constraints",
    "Knowledge placement",
)

ADMITTED = {"grepai", "serena", "tree-sitter", "scip", "sqlite"}

# ed3c/skill-concerns#76: every admitted tool declares what this skill requires
# of it and what makes it present. `path` is a binary this bundle resolves
# itself; `ambient` is a host service or foreign probe it deliberately does not
# pin and therefore must name a prerequisite. A tool with neither is the
# undeclared-ambient defect, so the shape is read here rather than trusted.
PRESENCE_KINDS = {"path", "ambient"}
PRESENCE_REQUIRED = {"path": ("probe", "requires"), "ambient": ("probe", "requires", "prerequisite")}


def check_environment_contract(topo: dict) -> list[str]:
    """The stack's environment declaration, read rather than assumed.

    Shape only, and deliberately: whether `grepai` is on this host is a
    question for `code_intel_driver.py --preflight` on the machine that will
    use it, not for a hermetic gate that would then red on every CI runner.
    What is decidable from bytes is that each admitted tool SAYS what it needs
    and what makes it present.
    """
    errors: list[str] = []
    contract = topo.get("environment_contract")
    if not isinstance(contract, dict) or not contract.get("checked_by"):
        errors.append("L1 declares no environment_contract naming what checks presence")
    tools = topo.get("tools", {})
    for name in sorted(ADMITTED):
        tool = tools.get(name)
        if not isinstance(tool, dict):
            continue  # the missing-tool error is already raised by validate()
        presence = tool.get("presence")
        if not isinstance(presence, dict):
            errors.append(f"tool {name!r} consumes the environment with no presence declaration")
            continue
        kind = presence.get("kind")
        if kind not in PRESENCE_KINDS:
            errors.append(f"tool {name!r} presence kind {kind!r} is not one of {sorted(PRESENCE_KINDS)}")
            continue
        for field in PRESENCE_REQUIRED[kind]:
            if not presence.get(field):
                errors.append(f"tool {name!r} {kind} presence declaration lacks {field!r}")
    return errors


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
    producer = need("scripts/gen_receipts.py")
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
        errors.extend(check_environment_contract(topo))

    receipts = {}
    if receipts_p:
        receipts = json.loads(receipts_p.read_text(encoding="utf-8")).get("evidence", {})
        if not receipts:
            errors.append("receipts.json has no evidence")
        for key in ("cross-repo-verified", "pgvector-built-pg16", "connected-not-usable", "lancedb-dropped"):
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
            errors.append(checked.stdout.strip() or "gen_receipts.py --check refused")

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
