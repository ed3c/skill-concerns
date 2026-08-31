#!/usr/bin/env python3
"""Bind the Drive-held campaign evidence archive into the pilot receipt."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = ROOT / "skills/spatial-loop-grounded/evals/behavioral-campaigns/2026-08-31-pilot.json"
d = json.loads(p.read_text())
d["evidence_archive"] = {
    "contents": "instrumented fixture bins + .ops call logs, unfalsified attempts.log, and the actor-authored quarantine.md - the judge's physical oracles, complete bytes",
    "sha256": "83534624f6fe7187de0351b8fead331c6f82b1bb99ea2ef002342cc026645846",
    "bytes": 2287,
    "drive_file_id": "1hUHciHSHVsczY8LnfDrD3jJwh-gfLeGr",
    "drive_url": "https://drive.google.com/file/d/1hUHciHSHVsczY8LnfDrD3jJwh-gfLeGr/view",
    "note": "full bytes on Drive (account-private); verify by downloading and recomputing sha256 against this receipt - the receipt is the tamper anchor",
}
p.write_text(json.dumps(d, indent=2) + "\n")
print("evidence archive bound into pilot receipt")
