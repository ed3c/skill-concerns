#!/usr/bin/env python3
"""CLI for the content-bound control-noodle composed contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from control_contract import ContractError, validate_bundle


# Count tie to this Skill's own entrypoint (ed3c/skill-concerns#74): the exact
# `## ` section headings of SKILL.md. This CLI validates composition data and
# never reads SKILL.md, so without this tuple the entrypoint could lose its
# Monitor mode or its hard constraints with the composed contract still green.
# `scripts/check_skill_bundles.py` reads it out of these bytes, parsed and never
# imported.
SKILL_MD_CLAUSES = (
    "Decision boundary",
    "Knowledge placement",
    "Failure-edge routing",
    "Monitor mode",
    "Hard constraints",
    "Soft conventions",
    "Discoverable knowledge",
    "Hermetic authoring",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--composition", required=True, type=Path)
    parser.add_argument("--feature-map", required=True, type=Path)
    parser.add_argument("--code-map", required=True, type=Path)
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--adapter", required=True, type=Path)
    parser.add_argument("--change-set", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--procedure-admission", required=True, type=Path)
    parser.add_argument("--source-lock", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_bundle(
            composition=load(args.composition),
            feature_map=load(args.feature_map),
            code_map=load(args.code_map),
            mapping=load(args.mapping),
            adapter=load(args.adapter),
            change_set=load(args.change_set),
            plan=load(args.plan),
            procedure_admission=load(args.procedure_admission),
            source_lock=load(args.source_lock),
        )
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(exc)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
