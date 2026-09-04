from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED_HEADINGS = (
    "## Context Model",
    "## Core Architecture Rules",
    "## Enforcement Hierarchy",
    "## Shortest Path Should Be the Best Path",
    "## Greenfield Systems",
    "## Human Slop and Agent Slop",
    "## Rewrite Safety",
    "## Adding New Architecture",
    "## Implementation Procedure",
    "## Best Path Decision Rule",
)

FORBIDDEN_BLACK_BOX_TOKENS = (
    "Noodle-owned",
    "noodles-component",
    "P/L/R/N",
    "FeatureMap",
    "Spatial Loop",
    "context-pack.json",
    "evidence-manifest.json",
    "authority_ceiling",
)

LOAD_BEARING_PHRASES = (
    "locally obvious change",
    "globally correct change",
    "strongest practical enforcement layer",
    "one obvious writer",
    "isolated extension",
    "Repeated human correction",
    "executable migration contract",
    "new layer that makes every future Agent understand more concepts",
    "Do not choose the shortest path merely because it compiles",
)


def validate(text: str) -> list[str]:
    errors: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading}")
    for token in FORBIDDEN_BLACK_BOX_TOKENS:
        if token in text:
            errors.append(f"rendered hot path leaks black-box/compiler vocabulary: {token}")
    for phrase in LOAD_BEARING_PHRASES:
        if phrase not in text:
            errors.append(f"load-bearing Best Path semantic missing: {phrase}")
    if "## Evidence lookup" in text or "claim_id" in text:
        errors.append("rendered product exposes evidence/compiler machinery in the hot path")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    text = args.path.read_text(encoding="utf-8")
    errors = validate(text)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
