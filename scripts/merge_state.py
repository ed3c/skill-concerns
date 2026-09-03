#!/usr/bin/env python3
"""Resolve one pull request's mergeability into an exit, never into a skip.

ed3c/skill-concerns#111. `verify.yml` grades `pull_request.head.sha`; the tree
that actually becomes `main` is `refs/pull/<n>/merge`, and the green tick is
read as "main stays green after this lands". Those are the same statement only
while the base has not moved since the head was built, which is the one
condition nothing checked.

Grading the merge result needs the merge ref, and the provider computes that
ref asynchronously: the first read after a `pull_request_target` event is
normally `mergeable: null` / `mergeable_state: "unknown"`. A job that reads it
once and treats `unknown` as "nothing to check" reproduces the blindness one
layer down, so this module gives every terminal state its own exit and gives
none of them a skip:

    MERGEABLE    exit 0   the merge ref exists; check it out and grade it
    UNMERGEABLE  exit 3   the provider says the two heads conflict
    UNKNOWN      exit 4   still uncomputed when the polling budget ran out
    UNREADABLE   exit 5   the provider never answered (auth, rate limit, 5xx)

UNKNOWN and UNREADABLE are separate on purpose: "the answer is not ready" and
"nobody answered" are the two states a single silent green would collapse, and
keeping absence apart from unreachability is this repository's standing rule
for every provider read (the cadence sweep's `ref_state` draws the same line).

`classify()` is a pure function of the provider's two fields and `resolve()`
takes its reader as an argument, so both directions are falsifiable with no
network at all -- `--selftest` is that falsifier.

WHY THIS JOB IS KEPT ALONGSIDE BRANCH PROTECTION (ed3c/skill-concerns#139)
-------------------------------------------------------------------------
The other mechanism, named here because nothing else in this repository names
it: `main` is protected with `required_status_checks.strict = true` --
"Require branches to be up to date before merging" -- with `enforce_admins`
enabled. Read, not inferred, 2026-09-03:

    $ gh api repos/ed3c/skill-concerns/branches/main/protection
    "required_status_checks": {"strict": true, "contexts": ["verify"]}
    "enforce_admins": {"enabled": true}

While `strict` holds, a head that merges already contains `main`'s tip, so
`refs/pull/<n>/merge` fast-forwards and the merge tree IS the head tree. #139
asked whether that makes this job redundant. Measured across every `verify` run
since ed3c/skill-concerns#111 landed as PR136
(`e96f4daf65dde684146756c1ab70031fba323f94`), 10 runs:

    merge-result concluded success        10/10
    merge-result agreed with verify        9/10
    disagreement: run 33687272813 (head 52c10f4159b9)
        merge-result=success, verify=failure, verify job 100439109014 step 7
        "Run trusted validators against the candidate tree"

So the two are not one gate seen twice, and the reason is structural rather than
incidental: `merge-result` grades the merge tree with the CANDIDATE's own
`run_all.py`, while `verify` step 7 runs `.trusted/scripts/*` from the default
branch against the candidate as data. A green merge-result is the candidate's
gate agreeing with itself on a third tree; it can never stand in for the
trusted-bytes pass. `test_the_two_mechanisms_are_not_one_gate_seen_twice` is
where that split is read off the workflow rather than asserted here.

Cost, measured over the same 10 runs rather than estimated: this job averaged
148.4s (29 billed runner-minutes total), against 147.6s for
`candidate-self-tests`. It is very nearly a second full gate run, and it is
spent knowingly.

The three exits #139 offered, and why this is exit 1:

  1. KEEP BOTH, say why here.  TAKEN. `strict` is branch-protection state:
     outside the repo, unversioned, changeable without a commit or a review. If
     it is ever turned off, this job is what remains in bytes.
  2. Promote `merge-result` to the required context and turn `strict` off.
     REFUSED, and not on taste. `verify.yml` triggers on
     `pull_request_target: [opened, synchronize, reopened, ready_for_review]` --
     no event there fires when the BASE moves. A check run is attached to
     `head.sha`, so a green `merge-result` stays green after `main` advances
     while `refs/pull/<n>/merge` silently becomes a different tree. Dropping
     `strict` would reopen the exact stale-base hole #111 exists to close, one
     level up, and it would move the required context onto candidate-supplied
     gate bytes -- the cook self-approving, which the trust split above forbids.
  3. Drop this job and record `strict` as the mechanism, with a reader that
     reds if it is disabled. REFUSED HERE, not on merit: it needs a cadence
     reader for a provider setting, which is ed3c/skill-concerns#134's subject.
     Until that lands, `strict` has no reader, and a guarantee nobody
     re-resolves is the `arrival-engineering` A4 shape this repository files
     against elsewhere.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import Callable

MERGEABLE = "MERGEABLE"
UNMERGEABLE = "UNMERGEABLE"
UNKNOWN = "UNKNOWN"
UNREADABLE = "UNREADABLE"

# The reader is `verify.yml`'s `mergeability` step, and only that: it runs this
# module and the shell fails the `merge-result` job on any non-zero. `land.yml`
# does not name this module at all -- it is triggered by `workflow_run` on a
# COMPLETED verify, so the refusal has already happened upstream of it, and a
# comment claiming it as a reader would be a reader that does not exist.
# Nothing here may return 0 for a state other than MERGEABLE.
#
# No process branches on 3 vs 4 vs 5; that step fails identically on all three.
# The distinction that IS read travels as the state WORD this module appends to
# `--github-output`, which `verify` prints as
# `MERGE_RESULT_UNGRADED:<result>:<state>` -- that is what makes a conflicting
# PR, an uncomputed one and an unreachable provider three different refusals
# instead of one green. The word is written before the exit, so a failing run
# still names its state (`test_the_state_word_survives_a_failing_exit`).
# The integers keep the same split for a CLI caller that has no
# `$GITHUB_OUTPUT` to read; ed3c/skill-concerns#111's absence control is what
# requires the split to exist at all, in either channel.
EXITS = {MERGEABLE: 0, UNMERGEABLE: 3, UNKNOWN: 4, UNREADABLE: 5}

# States worth waiting on. Everything else is terminal on the first read.
PENDING = (UNKNOWN, UNREADABLE)


def classify(mergeable: object, mergeable_state: object) -> str:
    """The provider's two fields -> one state name.

    `mergeable_state` leads because it is the field the provider uses to say
    "not computed yet" (`unknown`) and "the heads conflict" (`dirty`) in words.
    `mergeable` is the boolean behind it and decides the rest: `true` with
    `blocked`, `unstable` or `behind` all mean the merge ref exists and can be
    graded, and those are the ordinary states of a PR waiting on its own checks.
    Anything that is neither a bool nor a state we recognise is UNKNOWN rather
    than optimistically mergeable -- a shape nobody anticipated must not fall
    through to the exit that lets a land proceed.
    """
    if mergeable_state == "unknown":
        return UNKNOWN
    if mergeable_state == "dirty" or mergeable is False:
        return UNMERGEABLE
    if mergeable is True:
        return MERGEABLE
    return UNKNOWN


def read_pull(repository: str, number: int) -> tuple[str, str]:
    """One provider read -> (state, detail). Never raises on a failed read."""
    probe = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repository}/pulls/{number}",
            "--jq",
            "{mergeable: .mergeable, mergeable_state: .mergeable_state}",
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        tail = (probe.stdout + probe.stderr).strip().splitlines()
        return UNREADABLE, " | ".join(tail[-2:]) or f"gh exit {probe.returncode}"
    try:
        payload = json.loads(probe.stdout)
    except json.JSONDecodeError as exc:
        return UNREADABLE, f"unparseable provider payload: {exc}"
    state = classify(payload.get("mergeable"), payload.get("mergeable_state"))
    return state, f"mergeable={payload.get('mergeable')!r} mergeable_state={payload.get('mergeable_state')!r}"


def resolve(
    read: Callable[[], tuple[str, str]],
    attempts: int = 10,
    delay: float = 6.0,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[str, str]:
    """Poll `read` until it stops being pending, or until the budget runs out.

    The budget is what turns "not ready" into a decision instead of into an
    unbounded wait. Whatever the last read said is what is reported, so a run
    that timed out on UNREADABLE does not get re-labelled UNKNOWN.
    """
    state, detail = read()
    for _ in range(max(0, attempts - 1)):
        if state not in PENDING:
            return state, detail
        sleep(delay)
        state, detail = read()
    return state, detail


def selftest() -> int:
    """Planted both directions: each state reachable, each exit distinct."""
    checks: list[tuple[str, bool, str]] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append((name, passed, detail))

    table = (
        ((True, "clean"), MERGEABLE),
        ((True, "unstable"), MERGEABLE),
        ((True, "behind"), MERGEABLE),
        ((True, "blocked"), MERGEABLE),
        ((False, "dirty"), UNMERGEABLE),
        ((False, "clean"), UNMERGEABLE),
        ((None, "dirty"), UNMERGEABLE),
        ((None, "unknown"), UNKNOWN),
        ((True, "unknown"), UNKNOWN),
        ((None, None), UNKNOWN),
        (("yes", "clean"), UNKNOWN),
    )
    for (mergeable, state), expected in table:
        record(
            f"classify({mergeable!r},{state!r})=={expected}",
            classify(mergeable, state) == expected,
            f"got {classify(mergeable, state)}",
        )

    record(
        "every_state_has_its_own_exit_code",
        len(set(EXITS.values())) == len(EXITS) and EXITS[MERGEABLE] == 0,
        f"exits={EXITS}",
    )
    record(
        "only_mergeable_exits_zero",
        [name for name, code in EXITS.items() if code == 0] == [MERGEABLE],
        f"exits={EXITS}",
    )

    # The async window: unknown then unknown then the real answer.
    answers = [(UNKNOWN, "computing"), (UNKNOWN, "computing"), (MERGEABLE, "clean")]
    seen: list[str] = []

    def replay() -> tuple[str, str]:
        state, detail = answers[len(seen)]
        seen.append(state)
        return state, detail

    resolved, _ = resolve(replay, attempts=5, delay=0, sleep=lambda _: None)
    record(
        "a_late_answer_is_waited_for_not_read_as_nothing_to_check",
        resolved == MERGEABLE and len(seen) == 3,
        f"resolved={resolved} reads={seen}",
    )

    # Planted negative: an answer that never arrives must NOT become MERGEABLE.
    never = resolve(
        lambda: (UNKNOWN, "still computing"), attempts=3, delay=0, sleep=lambda _: None
    )
    record(
        "an_unanswered_budget_reports_unknown_and_never_green",
        never[0] == UNKNOWN and EXITS[never[0]] != 0,
        f"resolved={never}",
    )
    unreadable = resolve(
        lambda: (UNREADABLE, "HTTP 502"), attempts=2, delay=0, sleep=lambda _: None
    )
    record(
        "an_unreadable_provider_stays_unreadable_not_unknown",
        unreadable[0] == UNREADABLE,
        f"resolved={unreadable}",
    )
    # And a conflict is terminal on the first read: polling a dirty PR ten
    # times would only delay the refusal.
    reads = 0

    def conflicted() -> tuple[str, str]:
        nonlocal reads
        reads += 1
        return UNMERGEABLE, "dirty"

    resolve(conflicted, attempts=9, delay=0, sleep=lambda _: None)
    record("a_conflict_is_terminal_on_the_first_read", reads == 1, f"reads={reads}")

    for name, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    failed = [name for name, passed, _ in checks if not passed]
    if failed:
        print(f"selftest FAILED: {failed}")
        return 1
    print("selftest OK: four states, four exits, and none of them a skip")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository")
    parser.add_argument("--pull", type=int)
    parser.add_argument("--attempts", type=int, default=10)
    parser.add_argument("--delay", type=float, default=6.0)
    parser.add_argument(
        "--github-output",
        help="append `merge_state=<STATE>` here so the job that follows reads "
        "the same word this process exited on",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.repository or args.pull is None:
        parser.error("--repository and --pull are required without --selftest")

    state, detail = resolve(
        lambda: read_pull(args.repository, args.pull), args.attempts, args.delay
    )
    print(f"merge_state={state} {detail}")
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as handle:
            handle.write(f"merge_state={state}\n")
    return EXITS[state]


if __name__ == "__main__":
    raise SystemExit(main())
