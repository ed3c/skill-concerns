#!/usr/bin/env python3
"""Validate the complete bounded AGENTS.md routing graph."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys

from common import REPO_ROOT, load_json, print_result, safe_repo_path


MARKER = re.compile(r"<!--\s*agent-next:\s*(.*?)\s*-->", re.IGNORECASE)


def marker_routes(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    matches = MARKER.findall(text)
    if len(matches) != 1:
        return [], [f"AGENT_ROUTE_MARKER_COUNT:{path}:{len(matches)}"]
    raw = matches[0].strip()
    if raw.lower() == "none":
        return [], []
    routes = [item.strip() for item in raw.split(",") if item.strip()]
    if not routes:
        errors.append(f"AGENT_ROUTE_MARKER_EMPTY:{path}")
    return routes, errors


def check(root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    try:
        contract = load_json(root / "agents-routing.json")
    except ValueError as exc:
        return [str(exc)]

    if contract.get("schema_version") != 1:
        errors.append("AGENT_ROUTE_SCHEMA_VERSION")
    root_node = contract.get("root")
    max_documents = contract.get("max_documents")
    routes = contract.get("routes")

    if not isinstance(root_node, str):
        errors.append("AGENT_ROUTE_ROOT_INVALID")
        return errors
    if not isinstance(max_documents, int) or max_documents < 1:
        errors.append("AGENT_ROUTE_MAX_DOCUMENTS_INVALID")
    if not isinstance(routes, dict):
        errors.append("AGENT_ROUTES_NOT_OBJECT")
        return errors

    scanned = {
        path.relative_to(root).as_posix()
        for path in root.rglob("AGENTS.md")
        if ".git" not in path.parts
    }
    declared = set(routes)
    for path in sorted(scanned - declared):
        errors.append(f"AGENT_ROUTE_UNDECLARED_DOCUMENT:{path}")
    for path in sorted(declared - scanned):
        errors.append(f"AGENT_ROUTE_DECLARED_DOCUMENT_ABSENT:{path}")

    for node, children in routes.items():
        if not isinstance(children, list) or any(
            not isinstance(child, str) for child in children
        ):
            errors.append(f"AGENT_ROUTE_CHILDREN_INVALID:{node}")
            continue
        try:
            node_path = safe_repo_path(root, node)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not node_path.is_file():
            continue
        observed, marker_errors = marker_routes(node_path)
        errors.extend(marker_errors)
        if observed != children:
            errors.append(
                f"AGENT_ROUTE_MARKDOWN_DRIFT:{node}:"
                f"declared={children}:observed={observed}"
            )
        for child in children:
            if child not in routes:
                errors.append(f"AGENT_ROUTE_CHILD_UNDECLARED:{node}:{child}")

    if root_node not in routes:
        errors.append(f"AGENT_ROUTE_ROOT_ABSENT:{root_node}")
        return errors

    visiting: set[str] = set()
    visited: set[str] = set()
    reachable: set[str] = set()

    def walk(node: str, stack: list[str]) -> None:
        if node in visiting:
            errors.append(f"AGENT_ROUTE_CYCLE:{'->'.join(stack + [node])}")
            return
        if node in visited:
            reachable.add(node)
            return
        visiting.add(node)
        reachable.add(node)
        path = stack + [node]
        if isinstance(max_documents, int) and len(path) > max_documents:
            errors.append(
                f"AGENT_ROUTE_DEPTH:{len(path)}:{'->'.join(path)}"
            )
        children = routes.get(node, [])
        if isinstance(children, list):
            for child in children:
                if isinstance(child, str) and child in routes:
                    walk(child, path)
        visiting.remove(node)
        visited.add(node)

    walk(root_node, [])
    for node in sorted(declared - reachable):
        errors.append(f"AGENT_ROUTE_UNREACHABLE:{node}")

    # The collection policy requires every Skill root and forbids deeper files.
    skill_root = root / "skills"
    if skill_root.is_dir():
        for skill_dir in sorted(path for path in skill_root.iterdir() if path.is_dir()):
            expected = (skill_dir / "AGENTS.md").relative_to(root).as_posix()
            if expected not in routes:
                errors.append(f"SKILL_AGENT_ROUTE_ABSENT:{expected}")
            nested = [
                path
                for path in skill_dir.rglob("AGENTS.md")
                if path != skill_dir / "AGENTS.md"
            ]
            for path in nested:
                errors.append(
                    f"SKILL_AGENT_DOCUMENT_NESTED:"
                    f"{path.relative_to(root).as_posix()}"
                )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    return print_result("agents-routing", check(args.root.resolve()))


if __name__ == "__main__":
    raise SystemExit(main())
