#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
p = ROOT / "registry.json"
d = json.loads(p.read_text())
entry = {
    "name": "spatial-loop-grounded",
    "path": "skills/spatial-loop-grounded",
    "kind": "procedure-rich",
    "status": "ADMITTED",
    "manifest": "skills/spatial-loop-grounded/skill.json",
    "source_lock": "intake/spatial-loop-grounded/source-lock.json",
    "admission": "admissions/spatial-loop-grounded.json",
    "evidence_ceiling": "L3_HERMETIC",
}
if not any(s.get("name") == "spatial-loop-grounded" for s in d["skills"]):
    d["skills"].append(entry)
p.write_text(json.dumps(d, indent=2) + "\n")
print("registry updated")
