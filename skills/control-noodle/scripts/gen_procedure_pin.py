#!/usr/bin/env python3
"""Regenerate control-noodle's two feature-map-engineering tree-digest pins.

Root cause of ed3c/skill-concerns#74's slg-conduct finding: `domain/
composition.json:procedure_tree_sha256` and `fixtures/valid/procedure-
admission.json:skill_tree_sha256` were two hand-typed copies of a value that
already has a real producer -- `admissions/feature-map-engineering.json`,
written by `skills/feature-map-engineering/scripts/gen_admission.py`. This
script closes the gap: it reads that producer's output and writes both
mirrors from it, so a future feature-map-engineering re-admission is one
command here instead of two hand edits (spatial-loop-grounded C5).

Anchor-unique text replace, not a full re-dump: preserves each file's
existing formatting exactly, changing only the digest value.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

# The content-digest identity is declared once (ed3c/skill-concerns#112).
from common import HEX64  # noqa: E402

PRODUCER = ROOT / "admissions" / "feature-map-engineering.json"
TARGETS = {
    ROOT / "skills/control-noodle/domain/composition.json": "procedure_tree_sha256",
    ROOT / "skills/control-noodle/fixtures/valid/procedure-admission.json": "skill_tree_sha256",
}


def main() -> int:
    digest = json.loads(PRODUCER.read_text(encoding="utf-8")).get("skill_tree_sha256")
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        print(f"REFUSED: {PRODUCER} skill_tree_sha256 is not a 64-hex digest")
        return 1

    for path, key in TARGETS.items():
        text = path.read_text(encoding="utf-8")
        pattern = re.compile(rf'("{key}"\s*:\s*")[0-9a-f]{{64}}(")')
        if len(pattern.findall(text)) != 1:
            print(f"REFUSED: {path}: {key} anchor count != 1")
            return 1
        text = pattern.sub(rf"\g<1>{digest}\g<2>", text, count=1)
        path.write_text(text, encoding="utf-8")
        written = json.loads(path.read_text(encoding="utf-8"))
        assert written[key] == digest, (path, key)
        print(f"wrote {path.relative_to(ROOT)}: {key} = {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
