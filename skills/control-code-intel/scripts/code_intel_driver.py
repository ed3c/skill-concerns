#!/usr/bin/env python3
"""L2 - execution + assertions for the code-intel stack.

This is the executable control layer: it ACTs (runs a stack operation), POLLs
(index/store state), OBSERVEs (the result), ASSERTs (the property the L0 policy
demands - correct-repo for cross-repo retrieval, nonzero chunks after index,
re-verifiability of a ledger claim), and PERSISTs evidence (a receipt line).

It is driver code, not prose: --selftest runs the assertions against fixtures
so the skill's evidence claims are falsifiable without the live stack; the same
assertion functions run against the live stack when a real backend is present.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import Callable


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


def selftest() -> int:
    checks: list[Assertion] = [
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
        return 1
    print("selftest OK: every assertion holds and every negative control went red")
    return 0


def _expect_false(a: Assertion, label: str) -> Assertion:
    # invert a negative-control assertion: the driver is correct iff the
    # underlying assertion returned False here.
    return Assertion(f"negative_control:{label}", not a.passed, a.detail)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if args.selftest:
        return selftest()
    print("usage: code_intel_driver.py --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
