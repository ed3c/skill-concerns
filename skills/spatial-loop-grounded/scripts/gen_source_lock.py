#!/usr/bin/env python3
"""Rebuild the spatial-loop-grounded source lock in this repo's convention:
locked_files are local intake files; the upstream skill is pinned via
method_references with git blob SHAs."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UP = Path("/Users/neon/skills-shared")
REPO = "https://github.com/ed3c/skills-shared.git"
COMMIT = subprocess.run(["git", "-C", str(UP), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()

proposal = ROOT / "intake/spatial-loop-grounded/SOURCE_PROPOSAL.md"
refs = []
for rel in ("SKILL.md", "evals.json", "AGENTS.md", "README.md"):
    path = f"skills/spatial-loop-systems-engineering/{rel}"
    blob = subprocess.run(["git", "-C", str(UP), "rev-parse", f"HEAD:{path}"], check=True, capture_output=True, text=True).stdout.strip()
    refs.append({"repository": REPO, "commit": COMMIT, "path": path, "blob_sha": blob})

lock = {
    "schema_version": 1,
    "skill": "spatial-loop-grounded",
    "source_kind": "owner-design-brief",
    "repository": None,
    "commit": None,
    "source_path": "intake/spatial-loop-grounded/SOURCE_PROPOSAL.md",
    "locked_files": [
        {
            "path": "intake/spatial-loop-grounded/SOURCE_PROPOSAL.md",
            "sha256": hashlib.sha256(proposal.read_bytes()).hexdigest(),
        }
    ],
    "method_references": refs,
}
out = ROOT / "intake/spatial-loop-grounded/source-lock.json"
out.write_text(json.dumps(lock, indent=2) + "\n")
print("wrote", out, "with", len(refs), "method references at", COMMIT[:9])
