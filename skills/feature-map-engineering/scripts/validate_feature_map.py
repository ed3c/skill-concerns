#!/usr/bin/env python3
"""Validate FeatureMap IR and a verification plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from feature_map import ContractError, validate_verification_plan


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
