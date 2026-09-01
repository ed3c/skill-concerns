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
SNAPSHOT_ID = re.compile(r"^Snapshot ID:\s*`?([^`\s]+)`?\s*$", re.MULTILINE)
COMMIT = re.compile(r"\b([0-9a-f]{40})\b")
CODE_LITERAL = re.compile(r'"([A-Z][A-Z0-9_]*):(?!\s)')
HEAD_SHA = re.compile(r"^[0-9a-f]{7,40}$")


def head_type(value: str) -> str:
    """`--head` is the only non-hermetic input; git's own minimum abbreviation
    length (7 hex chars) is the floor below which a prefix stops identifying
    one commit. Without this, `commit.startswith(head)` in check_freshness
    accepts a 1-character prefix -- or a head longer than any real commit --
    as a fresh match against any baseline sharing that character."""
    if not HEAD_SHA.match(value):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not 7-40 lowercase hex characters"
        )
    return value


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


def table_rows(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """Return (header cells, data rows) for the first table in these lines."""
    rows: list[list[str]] = []
    for line in lines:
        match = TABLE_ROW.match(line.strip())
        if not match or SEPARATOR.fullmatch(match.group(1)):
            continue
        rows.append([cell.strip() for cell in match.group(1).split("|")])
    return (rows[0], rows[1:]) if rows else ([], [])


def check(pack: Path, binding: dict[str, str], baseline: list[str] | None,
          topology: dict, head: str | None = None) -> list[str]:
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
        for row in table_rows(body)[1]:
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

    errors.extend(check_freshness(texts["README"], head))
    errors.extend(check_task_packets(texts.get("DRIFT")))
    return errors


def check_freshness(readme: str, head: str | None) -> list[str]:
    """A projection names the subject it was compiled over, in one voice.

    The snapshot id and the baseline commit are two statements of the same fact
    written by hand at different moments. A refresh that updates one and not the
    other leaves a pack that looks current and describes an older tree, which is
    exactly the failure a reader cannot see. Comparing them to each other catches
    it without any provider access; `--head` additionally catches the pack that
    is internally consistent and simply out of date.
    """
    errors: list[str] = []
    match = SNAPSHOT_ID.search(readme)
    if not match:
        return ["SNAPSHOT_ID_ABSENT:README"]
    snapshot = match.group(1)
    commits = COMMIT.findall(readme)
    if not commits:
        return ["BASELINE_COMMIT_ABSENT:README"]
    if not any(commit[:7] in snapshot for commit in commits):
        errors.append(f"STALE_PROJECTION:snapshot-id:{snapshot}")
    if head and not any(
        commit.startswith(head) or head.startswith(commit[:7]) for commit in commits
    ):
        errors.append(f"STALE_PROJECTION:head:{head}")
    return errors


def check_task_packets(drift: str | None) -> list[str]:
    """Candidate packets are proposals; each must say what it may not promote.

    A packet without that column is indistinguishable from an instruction, and a
    projection that emits instructions has become an actor.
    """
    if drift is None:
        return []
    for heading, body in sections(drift):
        lowered = heading.lower()
        if "packet" not in lowered or "candidate" not in lowered:
            continue
        header, rows = table_rows(body)
        try:
            column = next(
                index for index, cell in enumerate(header) if "forbidden" in cell.lower()
            )
        except StopIteration:
            return [f"TASK_PACKET_UNBOUNDED:header:{heading}"]
        errors = []
        if not rows:
            errors.append(f"TASK_PACKET_SECTION_ABSENT:{heading}:no packets")
        for row in rows:
            if column >= len(row) or not row[column]:
                errors.append(f"TASK_PACKET_UNBOUNDED:{row[0] if row else '?'}")
        return errors
    return ["TASK_PACKET_SECTION_ABSENT:DRIFT"]


def run(pack: Path, binding: dict[str, str], baseline: list[str] | None,
        head: str | None = None) -> list[str]:
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    return check(pack, binding, baseline, topology, head)


# --- selftest -------------------------------------------------------------


def _apply(root: Path, role: str, old: str | None, new: str | None) -> None:
    """Apply one mutation step. `old is None` deletes the role's file instead
    of editing it, to model PACK_ROLE_ABSENT / PACK_INCOMPLETE."""
    path = root / role
    if old is None:
        if not path.is_file():
            raise AssertionError(f"selftest fixture drifted: {role} already absent")
        path.unlink()
        return
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"selftest fixture drifted: {old!r} absent from {role}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _advertised_codes() -> set[str]:
    """Every check code this checker's own bytes can emit.

    Derived from the source text itself rather than from a hand-maintained
    ledger in the L1 topology: removing an emitted code and its ledger row
    together -- the exact DENOMINATOR_SHRINK shape this checker exists to
    catch in a pack -- would otherwise shrink this tie unnoticed too.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    return set(CODE_LITERAL.findall(source))


def selftest() -> int:
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    binding = dict(topology["pack_roles"])
    baseline = json.loads(FIXTURE_BASELINE.read_text(encoding="utf-8"))["denominator"]
    failures: list[str] = []

    positive = check(FIXTURE_PACK, binding, baseline, topology)
    if positive:
        failures.append(f"positive control failed: {positive}")

    # Each mutation models one mechanized planted negative from the L1 topology,
    # or a check no planted negative or STAGE-P0 row already exercises. Steps
    # run in order on one fixture copy; a step with old=None deletes the file.
    mutations = [
        ("PN-1", [("README.md", "| `SRC-METHOD` |", "| ~~dropped~~ |")],
         "SOURCE_UNDECLARED"),
        ("PN-2", [("DAG.md", "  C -> node-b", "  S -> node-b")],
         "EDGE_CLASS_COLLAPSE"),
        ("PN-3", [("DAG.md",
         "| context compilation | node-b |",
         "| stable requirements | node-spec |\n| context compilation | node-b |")],
         "DUPLICATE_WRITER"),
        ("PN-4", [("CLOSURE.md", "[SRC-PROVIDER, R_REFERENCE, N]",
         "[SRC-PROVIDER, R_REFERENCE, R]")], "EVIDENCE_PROMOTION"),
        ("PN-6", [("README.md", "| `SRC-PAPER` |", "| ~~dropped~~ |")],
         "DENOMINATOR_SHRINK"),
        # STAGE-P0 discriminations that no planted negative already covers.
        ("SP0-STALE", [("README.md", "Snapshot ID: `FIXTURE-0123456",
         "Snapshot ID: `FIXTURE-9999999")], "STALE_PROJECTION"),
        ("SP0-PACKET", [("DRIFT.md", "| do not infer a dependency from ancestry |",
         "|  |")], "TASK_PACKET_UNBOUNDED"),
        ("SP0-NO-SNAPSHOT", [("README.md", "Snapshot ID: `FIXTURE-0123456",
         "Compiled around `FIXTURE-0123456")], "SNAPSHOT_ID_ABSENT"),
        ("SP0-NO-BASELINE", [("README.md", "0123456789abcdef0123456789abcdef01234567",
         "an unrecorded commit")], "BASELINE_COMMIT_ABSENT"),
        ("SP0-NO-PACKETS", [("DRIFT.md", "## Candidate next packets",
         "## Later ideas")], "TASK_PACKET_SECTION_ABSENT"),
        # Codes only LAW-* rows named in prose, with no mutation proving they
        # fire -- the gap a prior selftest tie could not see (finding: the
        # tie's own denominator, built from three ledgers, silently excluded
        # these nine codes when `check` was renamed to `mechanized_as`).
        ("LAW-ROLE-ABSENT", [("SYSTEM.md", None, None)], "PACK_ROLE_ABSENT"),
        ("LAW-INCOMPLETE", [("README.md", None, None)], "PACK_INCOMPLETE"),
        ("LAW-DENOM-ABSENT", [("README.md",
         "| `SRC-BRIEF` | fixture owner order, digest `0000` | `OWNER_REQUIREMENT` "
         "| current task input |\n"
         "| `SRC-TREE` | fixture commit `0123456789abcdef0123456789abcdef01234567` "
         "| `REPOSITORY_FACT` | exact baseline |\n"
         "| `SRC-PROVIDER` | fixture provider readback at the snapshot time "
         "| `R_REFERENCE` | frozen provider denominator |\n"
         "| `SRC-METHOD` | fixture pinned method bytes | `METHOD_SOURCE` "
         "| procedure, not correctness |\n"
         "| `SRC-PAPER` | fixture article; bytes, URL, and hash unavailable "
         "| `EXTERNAL_CLAIM` plus `ABSENT` | not verified here |",
         "| (denominator emptied for selftest) |")], "DENOMINATOR_ABSENT"),
        ("LAW-ANCHOR-MISS", [("SYSTEM.md",
         "database, and it does not prove that an Agent read it. "
         "`[SRC-BRIEF, OWNER_REQUIREMENT, N]`",
         "database, and it does not prove that an Agent read it. "
         "`[SRC-BRIEF, OWNER_REQUIREMENT, N]`\n\n"
         "## Untagged addendum\n\n"
         "This paragraph names no source id and no classification.")],
         "SECTION_UNANCHORED"),
        ("LAW-CLASS-UNKNOWN", [("CLOSURE.md",
         "closes only the denominator its evidence lane covers. "
         "`[SRC-PROVIDER, R_REFERENCE, N]`",
         "closes only the denominator its evidence lane covers. "
         "`[SRC-PROVIDER, Q_REFERENCE, N]`")], "CLASSIFICATION_UNKNOWN"),
        ("LAW-AUTHORITY-UNKNOWN", [("TRACEABILITY.md",
         "cannot fill them. `[SRC-BRIEF, OWNER_REQUIREMENT, N]`",
         "cannot fill them. `[SRC-BRIEF, OWNER_REQUIREMENT, X]`")],
         "AUTHORITY_CLASS_UNKNOWN"),
        ("LAW-EDGE-GRAPH-ABSENT", [("DAG.md",
         "## Exact current completion graph",
         "## Exact current completion overview")], "EDGE_GRAPH_ABSENT"),
        ("LAW-UNOWNED-CONVERGENCE", [("DAG.md",
         "| context compilation | node-b | the current pack writer |",
         "| context compilation |  | the current pack writer |")],
         "UNOWNED_CONVERGENCE"),
        ("LAW-TRACE-GAP-RULE-ABSENT", [
         ("TRACEABILITY.md",
          "Missing segments are `TRACEABILITY_GAP`;",
          "Missing segments are unnamed;"),
         ("TRACEABILITY.md",
          "| source refresh | `SRC-PAPER` | none | `TRACEABILITY_GAP` |",
          "| source refresh | `SRC-PAPER` | none | unresolved |"),
         ], "TRACEABILITY_GAP_RULE_ABSENT"),
    ]
    declared = {
        negative["id"]
        for negative in topology["planted_negatives"]
        if negative["state"] == "MECHANIZED"
    }
    if not declared <= {name for name, *_ in mutations}:
        failures.append(
            f"topology MECHANIZED set {sorted(declared)} is not covered by selftest "
            f"mutations {sorted({m[0] for m in mutations})}"
        )
    # Every code this checker's bytes can emit must actually fire somewhere:
    # a code no mutation raises is an assertion nobody can trust. Sourced from
    # the checker's own text (see _advertised_codes), not from a hand-kept
    # ledger a JSON edit could shrink in step with the code it stops proving.
    advertised = _advertised_codes()

    raised: set[str] = set()
    for name, steps, expected in mutations:
        with tempfile.TemporaryDirectory(prefix="ccp-") as temp:
            root = Path(temp) / "pack"
            shutil.copytree(FIXTURE_PACK, root)
            for role, old, new in steps:
                _apply(root, role, old, new)
            errors = check(root, binding, baseline, topology)
            raised.update(error.split(":", 1)[0] for error in errors)
            if not any(error.startswith(expected) for error in errors):
                failures.append(f"{name}: {expected} not raised; got {errors}")

    # The one check that needs an outside fact: a pack that is internally
    # consistent and simply older than the head the consumer just read back.
    stale = check(FIXTURE_PACK, binding, baseline, topology, head="deadbeef")
    raised.update(error.split(":", 1)[0] for error in stale)
    if not any(error.startswith("STALE_PROJECTION:head") for error in stale):
        failures.append(f"--head mismatch did not raise STALE_PROJECTION:head; got {stale}")

    for code in sorted(advertised - raised):
        failures.append(f"advertised check {code} was never raised by any mutation")

    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print(
        f"PASS: check_context_pack selftest ({len(mutations)} mutations red, "
        f"{len(advertised)} advertised checks all fired)"
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
    parser.add_argument(
        "--head", metavar="SHA", type=head_type,
        help="the commit the consumer just read back (7-40 lowercase hex chars), "
             "to catch a stale projection",
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

    errors = run(args.pack, binding, baseline, args.head)
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print(f"PASS: context pack at {args.pack} satisfies the L0 laws it can be judged on")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
