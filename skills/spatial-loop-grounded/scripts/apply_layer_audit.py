#!/usr/bin/env python3
"""Record the three-layer conformance audit of the pilot campaign."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

p = ROOT / "skills/spatial-loop-grounded/evals/behavioral-campaigns/2026-08-31-pilot.json"
d = json.loads(p.read_text())
d["layers_exercised"] = {
    "L0_procedure": "TESTED - portable clauses demonstrably drove actor decisions in all three scenarios",
    "L1_domain_knowledge": "NOT TESTED - fixtures carried no capability/state/entry-point artifact; actors explored source under L0 policy, which is not L1 routing discipline",
    "L2_execution_assertions": "EVAL-OWNED - act/observe/persist belonged to the instrumented harness; actor-side L2 discipline was scored only via the C4 quarantine artifact",
}
if "architecture audit" not in " ".join(d["notes"]):
    d["notes"].append(
        "architecture audit: this pilot validates L0 clause behavior with an eval-owned L2 oracle; it does not claim three-layer conformance - see protocol v2 requirements"
    )
p.write_text(json.dumps(d, indent=2) + "\n")

b = ROOT / "skills/spatial-loop-grounded/evals/behavioral.json"
data = json.loads(b.read_text())
for s in data["scenarios"]:
    s["layers"] = ["L0"]
data["v2_requirements"] = {
    "L1": "each v2 scenario ships an explicit domain-knowledge artifact (capabilities, states, entry points) inside the fixture; rubric adds: actor consults it before acting and refuses unmapped entry points",
    "L2": "rubric adds actor-side execution discipline: evidence persisted by the actor, assertions bound to terminal observations, not just harness logs",
    "modes_as_layers": "procedure-rich = L0-only bundle; domain-rich = L1(+L2) bundle; composed = all three - one method, three layers, never two independent approaches",
}
b.write_text(json.dumps(data, indent=2) + "\n")
print("receipt + spec upgraded")
