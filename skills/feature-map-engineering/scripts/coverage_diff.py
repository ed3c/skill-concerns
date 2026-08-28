#!/usr/bin/env python3
"""Compare two valid FeatureMap IR documents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from feature_map import ContractError, coverage_diff


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"ABSENT:{path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"INVALID_JSON:{path}:{exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        result = coverage_diff(load_json(args.old), load_json(args.new))
    except ContractError as exc:
        for code in exc.codes:
            print(code, file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
