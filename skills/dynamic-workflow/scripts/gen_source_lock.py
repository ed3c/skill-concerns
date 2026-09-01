#!/usr/bin/env python3
"""Build the dynamic-workflow source lock (owner-design-brief kind)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = "dynamic-workflow"
proposal = ROOT / "intake" / SKILL / "SOURCE_PROPOSAL.md"
lock = {
    "schema_version": 1,
    "skill": SKILL,
    "source_kind": "owner-design-brief",
    "repository": None,
    "commit": None,
    "source_path": f"intake/{SKILL}/SOURCE_PROPOSAL.md",
    "locked_files": [
        {"path": f"intake/{SKILL}/SOURCE_PROPOSAL.md", "sha256": hashlib.sha256(proposal.read_bytes()).hexdigest()}
    ],
    "method_references": [],
}
out = ROOT / "intake" / SKILL / "source-lock.json"
out.write_text(json.dumps(lock, indent=2) + "\n")
print("wrote", out)
