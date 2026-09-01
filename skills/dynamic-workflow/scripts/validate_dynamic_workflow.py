#!/usr/bin/env python3
"""Deterministic validator for dynamic-workflow.

Fails closed unless the three layers are present and coherent: L0 supervision
policy, L1 dispatch-runtime topology covering BOTH runtimes, L2 liveness driver
whose selftest passes. Also enforces the three owner adjudications of
ed3c/skill-concerns#59 mechanically rather than in prose:

- boundary: L1 must POINT at the ceremony owner and must not restate it, so
  every term it declares as not-owned-here may appear exactly once in the file
  AND must actually appear in the claimed owner's bytes - a boundary that
  points at nothing is not a boundary;
- filing-not-reflex: the reader must stay a reader, so the driver may not carry
  a subprocess or filesystem-removal surface it could invoke maintenance with;
- trigger-not-apply: the driver must degrade its own report to `lens-suspect`
  and only SCHEDULE a maintenance pass (exercised by the test suite).

This is the hillclimb gate - edits may add runtimes and receipts, never silently
weaken the layer structure, the pointer discipline, or the K10 law.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Count tie to this Skill's own entrypoint (ed3c/skill-concerns#74): the exact
# `## ` section headings of SKILL.md. This CLI never reads SKILL.md itself,
# which is exactly why the tie has to be declared here -- without it a section
# could be lost with every check still green. `scripts/check_skill_bundles.py`
# reads this tuple out of these bytes, parsed and never imported, and reds on
# any drift.
SKILL_MD_CLAUSES = (
    "The one law",
    "Doctor — is this lane worth reading?",
    "Drive — observe a run",
    "Evidence — where the proof goes",
    "What a supervisor may say",
    "Two lenses on one lane",
    "Findings, and why this reader cannot fix itself",
    "Knowledge placement",
)

REQUIRED_CLASSES = {"complete", "healthy", "stalled-suspect", "dead"}
REQUIRED_RUNTIMES = {"claude-code-workflow", "codex-noodle-session"}
RUNTIME_KEYS = {
    "lane_index",
    "completion_notification",
    "liveness_source",
    "death_signatures",
    "stamped_fields_that_are_not_liveness",
    "observed",
}
REQUIRED_RECEIPTS = (
    "step-4-real-wave-observation",
    "claude-code-workflow-shapes",
    "codex-session-shapes",
    "falsely-alive-stamp",
    "still-running-not-crashed",
)
JUDGE_RULES = (
    "FILED DESTINATION",
    "NAME THE INVARIANT",
    "RUNNABLE RECEIPT",
    "ANSWERED-RESIDUE",
    "C7 LEGAL EXIT",
)
# A reader with no process-spawning or deletion surface cannot invoke a
# maintenance pass inline, whatever a future edit's intent.
READER_FORBIDDEN_SURFACE = ("subprocess", "os.system", "shutil.rmtree", "os.remove", "unlink(")


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    def need(rel: str) -> Path | None:
        path = root / rel
        if not path.is_file():
            errors.append(f"missing L-layer file: {rel}")
            return None
        return path

    l0 = need("references/portable-supervision-policy.md")
    l1 = need("domain/dispatch-runtime-topology.json")
    l2 = need("scripts/liveness_driver.py")
    monitor = need("references/prompts/monitor-prompt.md")
    judge = need("references/prompts/judge-prompt.md")
    receipts_path = need("receipts.json")
    need("SKILL.md")

    if l0:
        text = l0.read_text(encoding="utf-8")
        if "L0 procedural" not in text:
            errors.append("L0 policy does not declare itself the procedural layer")
        for rule in JUDGE_RULES:
            if rule not in text:
                errors.append(f"L0 policy is missing judge rule v3 {rule!r}")
        for clause in ("S0", "S1", "S2", "actor", "stage-boundary", "mid-flight"):
            if clause not in text:
                errors.append(f"L0 policy is missing the {clause!r} clause")

    if l1:
        raw = l1.read_text(encoding="utf-8")
        topology = json.loads(raw)

        classes = topology.get("classes", {})
        missing = REQUIRED_CLASSES - set(classes)
        if missing:
            errors.append(f"L1 topology missing lane classes: {sorted(missing)}")
        # K10, as data: age can never produce `dead`.
        dead = classes.get("dead", {})
        if dead.get("requires") != "death_signature":
            errors.append("L1 `dead` class must require a death_signature")
        if dead.get("age_alone_insufficient") is not True:
            errors.append("L1 `dead` class must record age_alone_insufficient")
        if classes.get("stalled-suspect", {}).get("never") != "dead":
            errors.append("L1 `stalled-suspect` must record that it never resolves to dead")
        if not isinstance(topology.get("stall_threshold_seconds"), int):
            errors.append("L1 topology has no integer stall_threshold_seconds")

        runtimes = topology.get("runtimes", {})
        for name in sorted(REQUIRED_RUNTIMES - set(runtimes)):
            errors.append(f"L1 topology missing runtime {name!r}")
        for name, entry in runtimes.items():
            for key in sorted(RUNTIME_KEYS - set(entry)):
                errors.append(f"L1 runtime {name!r} missing observable {key!r}")
            if not entry.get("death_signatures"):
                errors.append(f"L1 runtime {name!r} declares no death signature")

        # Adjudication 1: point at the ceremony owner, never restate it.
        boundary = topology.get("ceremony_boundary", {})
        if boundary.get("owner") != "control-noodle":
            errors.append("L1 ceremony_boundary must name control-noodle as owner")
        terms = boundary.get("not_owned_here")
        owner_path = boundary.get("owner_path")
        owner_text = None
        if isinstance(owner_path, str):
            owner_file = (l1.parent / owner_path).resolve()
            if owner_file.is_file():
                owner_text = owner_file.read_text(encoding="utf-8")
            else:
                errors.append(f"L1 ceremony_boundary owner_path {owner_path!r} does not resolve to a file")
        if not isinstance(terms, list) or not terms:
            errors.append("L1 ceremony_boundary declares no not_owned_here terms")
        else:
            for term in terms:
                if raw.count(term) != 1:
                    errors.append(
                        f"L1 restates ceremony term {term!r} ({raw.count(term)} occurrences); "
                        "point at control-noodle, never restate"
                    )
                if owner_text is not None and term not in owner_text:
                    errors.append(
                        f"L1 ceremony term {term!r} does not appear in the claimed owner "
                        f"{owner_path!r}; a boundary pointing at nothing is not a boundary"
                    )

    if monitor:
        text = monitor.read_text(encoding="utf-8")
        for clause in ("stalled-suspect", "Never report it as dead", "mid-flight"):
            if clause not in text:
                errors.append(f"monitor-prompt is missing the {clause!r} clause")

    if judge:
        text = judge.read_text(encoding="utf-8")
        for rule in JUDGE_RULES:
            if rule not in text:
                errors.append(f"judge-prompt is missing judge rule v3 {rule!r}")
        if "owner=dynamic-workflow" not in text:
            errors.append("judge-prompt does not file lens-drift findings to an owner")

    if receipts_path:
        receipts = json.loads(receipts_path.read_text(encoding="utf-8")).get("evidence", {})
        if not receipts:
            errors.append("receipts.json has no evidence")
        for key in REQUIRED_RECEIPTS:
            if key not in receipts:
                errors.append(f"receipts.json missing load-bearing receipt {key!r}")

    # Adjudication 2: the reader stays a reader.
    if l2:
        source = l2.read_text(encoding="utf-8")
        for surface in READER_FORBIDDEN_SURFACE:
            if surface in source:
                errors.append(
                    f"L2 driver carries the write/exec surface {surface!r}; a reader that can "
                    "spawn or delete can invoke maintenance inline (ed3c/skill-concerns#59)"
                )
        result = subprocess.run(
            [sys.executable, str(l2), "--selftest"], capture_output=True, text=True
        )
        if result.returncode != 0:
            errors.append("L2 driver selftest failed (assertions or negative controls did not hold)")

    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: dynamic-workflow three-layer structure, pointer discipline and K10 law intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
