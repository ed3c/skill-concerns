#!/usr/bin/env python3
"""Validate FeatureMap IR and a verification plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from feature_map import ContractError, validate_verification_plan


# Count tie to this Skill's own entrypoint (ed3c/skill-concerns#74): the exact
# `## ` section headings of SKILL.md. This CLI validates map+plan data and never
# reads SKILL.md itself, which is exactly why the tie has to be declared here --
# without it a 516-line procedure could lose a section with every check still
# green. `scripts/check_skill_bundles.py` reads this tuple out of these bytes,
# parsed and never imported, and reds on any drift.
SKILL_MD_CLAUSES = (
    "Core contract",
    "Separation of concerns",
    "Locate or construct the map",
    "Feature identity",
    "Feature decomposition",
    "Explore before constraining",
    "Knowledge classes",
    "Evidence hierarchy",
    "Verification procedure",
    "Coverage reduction",
    "Change impact",
    "Domain adapter contract",
    "Feature document schema",
    "FeatureMap IR",
    "Proof-plan contract",
    "Skip semantics",
    "Assertions",
    "Meta-assertions",
    "Updating the map",
    "Stop conditions",
    "Completion",
)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"ABSENT:{path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"INVALID_JSON:{path}:{exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        summary = validate_verification_plan(
            load_json(args.map), load_json(args.plan)
        )
    except ContractError as exc:
        for code in exc.codes:
            print(code, file=sys.stderr)
        return 1

    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
