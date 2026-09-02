#!/usr/bin/env python3
"""L2 - execution + assertions for the code-intel stack.

This is the executable control layer: it ACTs (runs a stack operation), POLLs
(index/store state), OBSERVEs (the result), ASSERTs (the property the L0 policy
demands - correct-repo for cross-repo retrieval, nonzero chunks after index,
re-verifiability of a ledger claim), and PERSISTs evidence (a receipt line).

It is driver code, not prose: --selftest runs the assertions against fixtures
so the skill's evidence claims are falsifiable without the live stack; the same
assertion functions run against the live stack when a real backend is present.

--preflight is the live path's entry gate (ed3c/skill-concerns#76). Every tool
this skill uses is declared in domain/code-intel-topology.json with what the
skill requires of it and how its presence is checked; the preflight resolves the
`path`-kind declarations and REFUSES, naming the tool, rather than letting a
missing binary arrive later disguised as a query that found nothing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable


TOPOLOGY = Path(__file__).resolve().parents[1] / "domain" / "code-intel-topology.json"

# Exit codes are the representation, so tool-absence and a negative result can
# never be read as each other: 1 is "an assertion went red" (the stack answered
# and the answer was wrong), 3 is "a declared tool is not here at all" (nothing
# was asked). Collapsing them is the exact confusion this atom exists to end.
EXIT_ASSERTION_RED = 1
EXIT_TOOL_ABSENT = 3

PRESENCE_KINDS = ("path", "ambient")


@dataclass
class Assertion:
    name: str
    passed: bool
    detail: str


def assert_connected_is_not_usable(returned_results: int) -> Assertion:
    # L0: connected != usable; a tool that returns nothing is not in use.
    return Assertion(
        "connected_is_not_usable",
        returned_results > 0,
        f"a capability is 'in use' only when a real query returns results (got {returned_results})",
    )


def assert_cross_repo_returns_correct_repo(query_repo: str, top_result_path: str) -> Assertion:
    # L2: a repo-distinctive query must surface its own repository, not another.
    ok = f"/{query_repo}/" in top_result_path or top_result_path.startswith(f"{query_repo}/")
    return Assertion(
        "cross_repo_returns_correct_repo",
        ok,
        f"query targeting {query_repo!r} top result {top_result_path!r} "
        + ("names the expected repo" if ok else "names a DIFFERENT repo - cross-repo not proven"),
    )


def assert_index_populated(chunk_count: int) -> Assertion:
    # L2: after an index/backend switch, the store must hold chunks; a
    # last_index_time stamp can make an empty store report 'already indexed'.
    return Assertion(
        "index_populated",
        chunk_count > 0,
        f"store chunk count {chunk_count} (zero after a backend switch means a stale last_index_time skip)",
    )


def assert_ledger_reverifiable(recorded_digest: str, current_digest: str) -> Assertion:
    # R-class: a stored evidence row is served only when its digest still
    # matches the current source bytes.
    ok = recorded_digest == current_digest
    return Assertion(
        "ledger_reverifiable",
        ok,
        "recorded evidence digest matches current bytes" if ok else "digest drift - evidence must not be served",
    )


def preflight(topology: dict, which: Callable[[str], str | None] = shutil.which) -> tuple[int, list[str]]:
    """Resolve every declared tool; refuse, naming it, when a `path` one is gone.

    `which` is injected so the decision is falsifiable without touching the
    process environment; the test suite exercises the same function through a
    real PATH instead, which is the arrival that matters for a live path.
    """
    lines: list[str] = []
    absent: list[str] = []
    for name, tool in sorted((topology.get("tools") or {}).items()):
        presence = tool.get("presence") if isinstance(tool, dict) else None
        kind = presence.get("kind") if isinstance(presence, dict) else None
        if kind not in PRESENCE_KINDS:
            absent.append(name)
            lines.append(
                f"TOOL_UNDECLARED:{name}: no presence declaration, so nothing says what "
                "makes this tool present or what the skill needs from it"
            )
            continue
        probe = presence.get("probe") or ""
        requires = presence.get("requires") or ""
        if kind == "ambient":
            lines.append(f"AMBIENT:{name}: {probe} - {presence.get('prerequisite') or ''}")
            continue
        resolved = which(probe) if probe else None
        if resolved:
            lines.append(f"PRESENT:{name}: {probe} -> {resolved}")
        else:
            absent.append(name)
            lines.append(f"TOOL_ABSENT:{name}: {probe!r} is not on PATH; requires {requires}")
    if absent:
        lines.append(
            f"preflight REFUSED: {len(absent)} declared tool(s) absent: {', '.join(absent)}. "
            "This is a missing tool, not a query that found nothing."
        )
        return EXIT_TOOL_ABSENT, lines
    lines.append("preflight OK: every declared tool is present or declared ambient")
    return 0, lines


def _preflight_controls() -> list[Assertion]:
    """Both directions of the refusal, over the real declaration bytes.

    A preflight that has only ever been run where the tools happen to exist has
    never refused anything, so the arm that matters is the absent one.
    """
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    present_code, present_lines = preflight(topology, which=lambda probe: f"/usr/bin/{probe}")
    absent_code, absent_lines = preflight(topology, which=lambda probe: None)
    named = [line for line in absent_lines if line.startswith("TOOL_ABSENT:")]
    return [
        Assertion(
            "preflight_passes_when_declared_tools_resolve",
            present_code == 0,
            f"every path-kind declaration resolved (exit {present_code})",
        ),
        Assertion(
            "preflight_refuses_and_names_the_absent_tool",
            absent_code == EXIT_TOOL_ABSENT and bool(named),
            f"exit {absent_code} with {len(named)} named tool(s): {named}",
        ),
        Assertion(
            "tool_absence_is_not_an_assertion_failure",
            EXIT_TOOL_ABSENT != EXIT_ASSERTION_RED,
            f"TOOL_ABSENT exits {EXIT_TOOL_ABSENT}, a red assertion exits {EXIT_ASSERTION_RED}",
        ),
    ]


def selftest() -> int:
    checks: list[Assertion] = [
        *_preflight_controls(),
        # positive controls (the properties that held tonight)
        assert_connected_is_not_usable(3),
        assert_cross_repo_returns_correct_repo("noodles", "code-intel/noodles/.github/workflows/land.yml:72-76"),
        assert_cross_repo_returns_correct_repo("skill-concerns", "code-intel/skill-concerns/skills/feature-map-engineering/references/evidence-contract.md:42-46"),
        assert_index_populated(1056),
        assert_ledger_reverifiable("abc123", "abc123"),
        # negative controls (each MUST fail, proving the assertions can go red)
        _expect_false(assert_connected_is_not_usable(0), "empty result is not usable"),
        _expect_false(assert_cross_repo_returns_correct_repo("noodles", "code-intel/skill-concerns/skills/README.md:1-8"), "wrong-repo top result"),
        _expect_false(assert_index_populated(0), "empty store"),
        _expect_false(assert_ledger_reverifiable("abc123", "def456"), "digest drift"),
    ]
    failed = [c for c in checks if not c.passed]
    for c in checks:
        print(f"[{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")
    if failed:
        print(f"selftest FAILED: {len(failed)} assertion(s) did not hold")
        return EXIT_ASSERTION_RED
    print("selftest OK: every assertion holds and every negative control went red")
    return 0


def _expect_false(a: Assertion, label: str) -> Assertion:
    # invert a negative-control assertion: the driver is correct iff the
    # underlying assertion returned False here.
    return Assertion(f"negative_control:{label}", not a.passed, a.detail)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument(
        "--preflight",
        action="store_true",
        help="resolve the declared stack before any live use; exits 3 naming an absent tool",
    )
    args = p.parse_args()
    if args.preflight:
        code, lines = preflight(json.loads(TOPOLOGY.read_text(encoding="utf-8")))
        for line in lines:
            print(line)
        return code
    if args.selftest:
        return selftest()
    print("usage: code_intel_driver.py [--selftest | --preflight]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
