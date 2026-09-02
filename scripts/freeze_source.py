#!/usr/bin/env python3
"""Freeze a source Skill from an already-bound local Git checkout.

This tool does not clone, fetch, or infer a branch. The caller supplies the
exact repository URL, 40-character commit, and local checkout bytes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import HEX40, digest_entries, regular_files


def build_lock(
    checkout: Path,
    repository: str,
    commit: str,
    source_path: str,
    skill: str,
) -> dict:
    if not checkout.is_dir():
        raise ValueError(f"CHECKOUT_ABSENT:{checkout}")
    if not HEX40.fullmatch(commit):
        raise ValueError("COMMIT_NOT_EXACT_40_HEX")
    if not repository:
        raise ValueError("REPOSITORY_MISSING")
    source = (checkout / source_path).resolve()
    checkout_resolved = checkout.resolve()
    if source != checkout_resolved and checkout_resolved not in source.parents:
        raise ValueError("SOURCE_PATH_ESCAPES_CHECKOUT")
    if not source.exists():
        raise ValueError(f"SOURCE_PATH_ABSENT:{source_path}")

    paths = [source] if source.is_file() else regular_files(source)
    if not paths:
        raise ValueError("SOURCE_FILES_EMPTY")
    entries = digest_entries(checkout_resolved, paths)
    return {
        "schema_version": 1,
        "skill": skill,
        "source_kind": "git",
        "repository": repository,
        "commit": commit,
        "source_path": source_path,
        "locked_files": entries,
        "method_references": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        lock = build_lock(
            args.checkout.resolve(),
            args.repository,
            args.commit,
            args.source_path,
            args.skill,
        )
    except ValueError as exc:
        print(exc)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
