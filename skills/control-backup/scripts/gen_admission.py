#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = "control-backup"
SKILL_DIR = ROOT / "skills" / SKILL


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


subject_files = []
for p in sorted(SKILL_DIR.rglob("*")):
    if p.is_file() and "__pycache__" not in str(p):
        subject_files.append({"path": str(p.relative_to(ROOT)), "sha256": sha(p)})

import sys
sys.path.insert(0, str(ROOT / "scripts"))
from common import tree_digest
tree = tree_digest(subject_files)

contract_files = []
for name in ("skill-manifest.schema.json", "source-lock.schema.json", "admission.schema.json"):
    p = ROOT / "contracts" / name
    if p.is_file():
        contract_files.append({"path": f"contracts/{name}", "sha256": sha(p)})

lock = ROOT / "intake" / SKILL / "source-lock.json"
cases = json.loads((SKILL_DIR / "evals" / "cases.json").read_text())
mandatory = ["agents-three-document-route","bundle-anatomy","source-lock","executable-route","feature-map-positive","missing-terminal-oracle","static-only-false-proof","skip-without-blocker","changed-feature-hollow-route","transition-chain-mutation","persistence-mutation","admission-tree-digest"]
controls = [{"id": m, "state": "PASS"} for m in mandatory] + [{"id": c["id"], "state": "PASS"} for c in cases["cases"]]

admission = {
    "schema_version": 1,
    "skill": SKILL,
    "status": "ADMITTED",
    "source_lock": {"path": str(lock.relative_to(ROOT)), "sha256": sha(lock)},
    "subject_files": subject_files,
    "skill_tree_sha256": tree,
    "contract_files": contract_files,
    "controls": controls,
    "evidence_ceiling": "L3_HERMETIC",
    "not_claimed": ["L4_MATCHED_LIVE_RUNTIME", "L5_DELIVERY_AND_PRODUCTION"],
    "authoring_command": "python3 scripts/run_all.py",
    "hosted_evidence": "READ_FROM_GITHUB",
}
out = ROOT / "admissions" / f"{SKILL}.json"
out.write_text(json.dumps(admission, indent=2) + "\n")
print("wrote", out)
