#!/usr/bin/env python3
"""Build the context-closure-engineering source lock (owner-design-brief kind).

The brief is locked by content digest. The method bytes it refactors stay in
their own repository and are locked by Git blob identity, read from the L1
topology so the two cannot drift apart.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = "context-closure-engineering"

proposal = ROOT / "intake" / SKILL / "SOURCE_PROPOSAL.md"
frozen = json.loads(
    (ROOT / "skills" / SKILL / "domain" / "context-closure-topology.json")
    .read_text(encoding="utf-8")
)["frozen_source"]

lock = {
    "schema_version": 1,
    "skill": SKILL,
    "source_kind": "owner-design-brief",
    "repository": None,
    "commit": None,
    "source_path": f"intake/{SKILL}/SOURCE_PROPOSAL.md",
    "locked_files": [
        {
            "path": f"intake/{SKILL}/SOURCE_PROPOSAL.md",
            "sha256": hashlib.sha256(proposal.read_bytes()).hexdigest(),
        }
    ],
    "method_references": [
        {
            "repository": frozen["repository"],
            "path": frozen["path_prefix"] + name,
            "commit": frozen["commit"],
            "blob_sha": blob,
        }
        for name, blob in sorted(frozen["blobs"].items())
    ],
}

out = ROOT / "intake" / SKILL / "source-lock.json"
out.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
print("wrote", out)
