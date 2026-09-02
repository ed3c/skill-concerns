#!/usr/bin/env python3
"""Build the shadow-architect source lock (owner-design-brief kind).

The brief is locked by content digest. The pstack ceremonies this bundle was
born under and is maintained by stay in their own repository and are locked by
Git blob identity, read from `policy/upstream-pins.json` so the lock and the
cadence sweep cannot name different bytes.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = "shadow-architect"

proposal = ROOT / "intake" / SKILL / "SOURCE_PROPOSAL.md"
pins = json.loads((ROOT / "policy" / "upstream-pins.json").read_text(encoding="utf-8"))
pstack = next(pin for pin in pins["pins"] if pin["id"] == "pstack-canonical-head")

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
            "repository": pstack["repository"],
            "path": watched["path"],
            "commit": pstack["pinned_commit"],
            "blob_sha": watched["blob_sha"],
        }
        for watched in sorted(pstack["watched_files"], key=lambda item: item["path"])
    ],
}

out = ROOT / "intake" / SKILL / "source-lock.json"
out.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
print("wrote", out)
