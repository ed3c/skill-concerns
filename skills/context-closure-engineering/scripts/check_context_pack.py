#!/usr/bin/env python3
"""L2 executable contract for a context-and-closure pack.

Judges shape, source binding, denominator, edge classes, writer identity, and
evidence ceiling. It does not judge natural-language design quality; that stays
P-class review. Every code below is a structural fact about the pack's bytes.

`--selftest` replays the mechanized planted negatives from the L1 topology: the
valid fixture must pass, and each mutation must produce its declared code. A
weakened assertion therefore goes red here before it can go green in a receipt.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = SKILL_ROOT / "domain" / "context-closure-topology.json"
FIXTURE_PACK = SKILL_ROOT / "evals" / "fixtures" / "pack"
FIXTURE_BASELINE = SKILL_ROOT / "evals" / "fixtures" / "baseline.json"

SOURCE_ID = re.compile(r"\bSRC-[A-Z0-9-]+")
ANCHOR = re.compile(r"\[(SRC-[A-Z0-9-]+)(?::[^\],]*)?,\s*([^,\]]+?),\s*([A-Z]+)\]")
DENOM_ROW = re.compile(r"^\|\s*`(SRC-[A-Z0-9-]+)`\s*\|")
TABLE_ROW = re.compile(r"^\|(.+)\|\s*$")
EDGE = re.compile(r"^ {2,}([A-Z]+)\s*->\s*\S")
HEADING = re.compile(r"^(#{2,})\s+(\S.*)$")
SEPARATOR = re.compile(r"^[\s:|-]+$")


def sections(text: str) -> list[tuple[str, list[str]]]:
    """Split a Markdown file into `##`-level sections: (heading, body lines)."""
    out: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in text.splitlines():
        match = HEADING.match(line)
        if match and len(match.group(1)) == 2:
            current = (match.group(2).strip(), [])
            out.append(current)
        elif current is not None:
            current[1].append(line)
    return out


def table_rows(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        match = TABLE_ROW.match(line.strip())
        if not match or SEPARATOR.fullmatch(match.group(1)):
            continue
        rows.append([cell.strip() for cell in match.group(1).split("|")])
    return rows[1:] if rows else rows  # drop the header row


def check(pack: Path, binding: dict[str, str], baseline: list[str] | None,
          topology: dict) -> list[str]:
    errors: list[str] = []

    files: dict[str, Path] = {}
    for role, name in binding.items():
        path = pack / name
        if not path.is_file():
            errors.append(f"PACK_ROLE_ABSENT:{role}:{name}")
            continue
        files[role] = path
    if "README" not in files or "DAG" not in files:
        return errors + ["PACK_INCOMPLETE:README and DAG are required to judge the rest"]

    texts = {role: path.read_text(encoding="utf-8") for role, path in files.items()}

    # LAW-DENOMINATOR: the README table is the closed source denominator.
    declared = [
        match.group(1)
        for line in texts["README"].splitlines()
        if (match := DENOM_ROW.match(line))
    ]
    if not declared:
        errors.append("DENOMINATOR_ABSENT:README carries no `SRC-*` denominator rows")
    declared_set = set(declared)
    for source_id in baseline or []:
        if source_id not in declared_set:
            errors.append(f"DENOMINATOR_SHRINK:{source_id}")

    # LAW-ANCHOR / LAW-NO-PROMOTION / LAW-EXTERNAL-CLAIM.
    #
    # A pack anchors statements in several shapes -- an inline `[id, class,
    # authority]` bracket, a table column, a trailing "Source: ..." sentence.
    # Enumerating idioms is a losing game, so the section rule asks only for the
    # two facts the law names: at least one declared source id and at least one
    # class token. The bracket form is additionally checked field by field.
    vocabulary = set(topology["classifications"])
    allowed = set(topology["anchor_authority_classes"])
    promoted = set(topology["promoted_authority_classes"])
    class_tokens = {*vocabulary, *(f"`{item}`" for item in allowed)}
    for role, text in texts.items():
        for source_id in set(SOURCE_ID.findall(text)) - declared_set:
            errors.append(f"SOURCE_UNDECLARED:{role}:{source_id}")
        for heading, body in sections(text):
            joined = "\n".join(body)
            anchors = ANCHOR.findall(joined)
            if not (SOURCE_ID.search(joined) and any(t in joined for t in class_tokens)):
                errors.append(f"SECTION_UNANCHORED:{role}:{heading}")
            for source_id, classification, authority in anchors:
                for token in classification.split(" plus "):
                    if token.strip().strip("`") not in vocabulary:
                        errors.append(
                            f"CLASSIFICATION_UNKNOWN:{role}:{source_id}:{token.strip()}"
                        )
                if authority in promoted:
                    errors.append(f"EVIDENCE_PROMOTION:{role}:{source_id}:{authority}")
                elif authority not in allowed:
                    errors.append(
                        f"AUTHORITY_CLASS_UNKNOWN:{role}:{source_id}:{authority}"
                    )

    # LAW-EDGE-SPLIT: a start graph may not carry completion edges, and a
    # completion graph may not carry start edges.
    completion_ok = set(topology["completion_edge_classes"])
    start_ok = set(topology["start_edge_classes"])
    seen_graph = {"completion": False, "start": False}
    for heading, body in sections(texts["DAG"]):
        lowered = heading.lower()
        if "completion graph" in lowered:
            kind, permitted = "completion", completion_ok
        elif "start-readiness graph" in lowered:
            kind, permitted = "start", start_ok
        else:
            continue
        seen_graph[kind] = True
        for line in body:
            match = EDGE.match(line)
            if match and match.group(1) not in permitted:
                errors.append(f"EDGE_CLASS_COLLAPSE:{kind}:{match.group(1)}:{heading}")
    for kind, seen in seen_graph.items():
        if not seen:
            errors.append(f"EDGE_GRAPH_ABSENT:{kind}")

    # LAW-ONE-CONVERGENCE-OWNER.
    owners_seen = False
    for heading, body in sections(texts["DAG"]):
        if "convergence owner" not in heading.lower():
            continue
        owners_seen = True
        concerns: set[str] = set()
        for row in table_rows(body):
            if len(row) < 2:
                continue
            concern, owner = row[0], row[1]
            if concern in concerns:
                errors.append(f"DUPLICATE_WRITER:{concern}")
            concerns.add(concern)
            if not owner:
                errors.append(f"UNOWNED_CONVERGENCE:{concern}")
    if not owners_seen:
        errors.append("EDGE_GRAPH_ABSENT:convergence-owners")

    # LAW-TRACE-GAP: an unavailable chain segment has a name in the pack.
    trace = texts.get("TRACEABILITY")
    if trace is not None and "TRACEABILITY_GAP" not in trace:
        errors.append("TRACEABILITY_GAP_RULE_ABSENT:TRACEABILITY")

    return errors


def run(pack: Path, binding: dict[str, str], baseline: list[str] | None) -> list[str]:
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    return check(pack, binding, baseline, topology)


# --- selftest -------------------------------------------------------------


def _mutate(root: Path, role: str, old: str, new: str) -> None:
    path = root / role
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"selftest fixture drifted: {old!r} absent from {role}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def selftest() -> int:
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    binding = dict(topology["pack_roles"])
    baseline = json.loads(FIXTURE_BASELINE.read_text(encoding="utf-8"))["denominator"]
    failures: list[str] = []

    positive = check(FIXTURE_PACK, binding, baseline, topology)
    if positive:
        failures.append(f"positive control failed: {positive}")

    # Each mutation models one mechanized planted negative from the L1 topology.
    mutations = [
        ("PN-1", "README.md", "| `SRC-METHOD` |", "| ~~dropped~~ |", "SOURCE_UNDECLARED"),
        ("PN-2", "DAG.md", "  C -> node-b", "  S -> node-b", "EDGE_CLASS_COLLAPSE"),
        ("PN-3", "DAG.md",
         "| context compilation | node-b |",
         "| stable requirements | node-spec |\n| context compilation | node-b |",
         "DUPLICATE_WRITER"),
        ("PN-4", "CLOSURE.md", "[SRC-PROVIDER, R_REFERENCE, N]",
         "[SRC-PROVIDER, R_REFERENCE, R]", "EVIDENCE_PROMOTION"),
        ("PN-6", "README.md", "| `SRC-PAPER` |", "| ~~dropped~~ |", "DENOMINATOR_SHRINK"),
    ]
    declared = {
        negative["id"]: negative
        for negative in topology["planted_negatives"]
        if negative["state"] == "MECHANIZED"
    }
    if {name for name, *_ in mutations} != set(declared):
        failures.append(
            f"selftest mutations {sorted({m[0] for m in mutations})} do not match "
            f"topology MECHANIZED set {sorted(declared)}"
        )

    for name, role, old, new, expected in mutations:
        with tempfile.TemporaryDirectory(prefix="ccp-") as temp:
            root = Path(temp) / "pack"
            shutil.copytree(FIXTURE_PACK, root)
            _mutate(root, role, old, new)
            errors = check(root, binding, baseline, topology)
            if not any(error.startswith(expected) for error in errors):
                failures.append(f"{name}: {expected} not raised; got {errors}")

    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print(
        f"PASS: check_context_pack selftest "
        f"({len(mutations)} mechanized planted negatives all went red)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, help="directory holding the pack files")
    parser.add_argument(
        "--bind", action="append", default=[], metavar="ROLE=FILE",
        help="override one consumer file-name binding",
    )
    parser.add_argument(
        "--baseline", type=Path,
        help='JSON {"denominator": [...]} from the previous pack, to catch a shrink',
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()
    if args.pack is None:
        parser.error("--pack is required unless --selftest is given")

    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    binding = dict(topology["pack_roles"])
    for item in args.bind:
        role, _, name = item.partition("=")
        if not name:
            parser.error(f"--bind expects ROLE=FILE, got {item!r}")
        binding[role] = name

    baseline = None
    if args.baseline is not None:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))["denominator"]

    errors = run(args.pack, binding, baseline)
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print(f"PASS: context pack at {args.pack} satisfies the L0 laws it can be judged on")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
