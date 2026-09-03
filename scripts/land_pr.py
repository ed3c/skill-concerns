#!/usr/bin/env python3
"""Land a verified pull request at its exact verified head and close its Issue.

Trust split: the receipt (produced by the trusted verify job) names *which*
commit was verified; policy/github.json on the default branch names the
repository, base branch and merge method. Nothing is taken from the candidate.

Everything after the merge is re-enterable (ed3c/skill-concerns#141)
-------------------------------------------------------------------

The merge is the one irreversible step, so every step after it is written to
survive being interrupted and re-run:

  1. the anchor is posted immediately after the merge readback, before
     anything that can fail non-atomically. It used to be last, so a refusal on
     the issue PATCH took it out and the merged pull request ended with no
     artifact a third party could check the landing against;
  2. `patch_issue()` treats a non-2xx whose effect may have applied as a state
     to re-read rather than as a fatal, because a provider can be wrong about
     its own effect. `PROVIDER_MISREPORTED` is the exit for that: the landing
     completed and the provider misreported, which must not share a report
     shape with the landing failing;
  3. `--resume` re-enters after the merge instead of exiting `PULL_NOT_OPEN`,
     so an interrupted landing is finished by the mechanism that owns the
     artifact rather than by hand. Its caller is `.github/workflows/land.yml`,
     which passes it on every attempt after the first -- an option no process
     resolves is prose, and re-running the job is the only recovery path this
     repository has after an irreversible step.

`PROVIDER_MISREPORTED` and a refusal both fail the Actions job, because Actions
has no tri-state step outcome. The re-entry is what separates them physically
rather than in a comment: after a landing that completed, `--resume` re-reads a
merged pull request, posts no second anchor and never merges again; after a run
that never got past the merge, it refuses `RESUME_NOT_MERGED:<n>:open`, so a
pre-merge failure is retried by re-running `verify` for a fresh receipt and
never by re-entering here. `tests/test_land_pr.py::ResumeAfterMergeTests
::test_the_re_entry_tells_landed_apart_from_never_landed` is that pair.

The instance this was found on is `ed3c/skill-concerns` PR 140
(`Refs ed3c/skill-concerns#81`, merge commit
`4428d757c127f79194153f46b34e091b267b8a57`, merged 2026-09-02T20:55:11Z). Its
issue PATCH answered 422 with an empty `errors` array *after applying in full*
-- body stamped, state closed, timeline recording the close in the same second
-- and the anchor was never written. It is still an anchorless merged pull
request; `tests/test_land_pr.py::ResumeAfterMergeTests` replays its recorded
shape (merged pull request, zero comments, issue already closed and stamped)
through `main(["--resume", ...])`, which is the path that backfills it. No
anchor was hand-written for it: a hand-typed line in the machine's format is
indistinguishable from the machine's, and the gap is the finding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


API = "https://api.github.com"
REFS_LINE = re.compile(r"^Refs\s+([A-Za-z0-9._-]+/[A-Za-z0-9._-]+)#(\d+)$")

# The landing completed and the provider misreported one of its own writes.
# Distinct from 0 (nothing to report) and from the SystemExit refusals (the
# landing did not complete), because a run that says only "failed" sends the
# next operator looking for damage there is none of, and a run that says only
# "landed" hides a provider answering 422 about a write it performed.
PROVIDER_MISREPORTED = 3


def body_digest(body: str | None) -> str:
    """sha256 of a provider-read body, full 64-hex, `null` read as empty.

    One definition, so the anchor's field and any independent recomputation are
    the same function of the same bytes: the body exactly as the provider
    returns it, UTF-8 encoded, no normalisation of line endings and no trailing
    newline added. A truncated digest is not a shorter version of this value,
    it is a different claim; `HEX64` in `scripts/common.py` is the pattern.
    """
    return hashlib.sha256((body or "").encode("utf-8")).hexdigest()


def parse_refs(body: str | None, repository: str) -> int:
    """Return the Issue number from the single 'Refs <owner>/<repo>#<n>' line."""
    hits = [
        match
        for match in (REFS_LINE.match(line.strip()) for line in (body or "").splitlines())
        if match
    ]
    if len(hits) != 1:
        raise SystemExit(f"REFS_LINE_COUNT:{len(hits)}")
    named, number = hits[0].group(1), int(hits[0].group(2))
    if named != repository:
        raise SystemExit(f"REFS_FOREIGN_REPOSITORY:{named}")
    return number


def stamp(body: str | None, markers: dict[str, str]) -> str:
    """Set each `<!-- noodles-<key>: ... -->` marker, replacing in place or appending."""
    text = body or ""
    for key, value in markers.items():
        line = f"<!-- noodles-{key}: {value} -->"
        text, replaced = re.subn(
            rf"^<!--\s*noodles-{re.escape(key)}:.*?-->[ \t]*$",
            lambda _match, line=line: line,
            text,
            count=1,
            flags=re.MULTILINE,
        )
        if not replaced:
            text = text.rstrip("\n") + "\n" + line + "\n"
    return text


def api(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:  # surface the provider's own reason
        raise SystemExit(
            f"GITHUB_API_REFUSED:{method}:{path}:{exc.code}:{exc.read().decode('utf-8', 'replace')}"
        ) from exc


def post_receipt_anchor(
    repository: str, number: int, merge_sha: str, call: Any = None
) -> str:
    """Post the physical-receipt anchor on the merged PR, once.

    N-class: runs after the merge readback and can never gate a land - every
    failure path returns 'failed' instead of raising. The Drive index is
    appended by the periodic batch reconcile, not here.
    Returns 'exists' | 'posted' | 'failed'.

    It runs BEFORE the issue PATCH rather than after the issue-closure readback
    (ed3c/skill-concerns#141). Being N-class stopped it gating a land; it did
    not stop a land from gating it, and a step that only ever ran last was
    unreachable the moment any earlier post-merge step raised. Ordering is what
    fixes that: this call depends on the merge and on nothing after it.

    Anchor format (ed3c/skill-concerns#77 appends the last field; the first
    three are unchanged, so existing consumers keep parsing what they parsed):

        physical-receipt-anchor: pr=<n> merge-commit=<sha> merged-at=<iso> \
body-sha256=<64-hex>

    `body-sha256` is `body_digest()` of the PR body this merge landed, read
    back from the provider inside this function. Every wave lane self-reports
    the digests of the bodies it wrote; this is the one field a reader can
    recompute without trusting the report. The check is one line, and an anchor
    whose field disagrees with it is the planted control:

        python3 -c 'import hashlib,json,subprocess as s;print(hashlib.sha256(
        (json.loads(s.check_output(["gh","api","repos/OWNER/REPO/pulls/N"]))
        ["body"] or "").encode()).hexdigest())'

    The PR body is stable across this landing: `main()` PATCHes the *Issue*
    body afterwards, never the pull request's.
    """
    call = api if call is None else call
    try:
        comments = call("GET", f"/repos/{repository}/issues/{number}/comments?per_page=100")
        if any(
            "physical-receipt-anchor" in str(item.get("body") or "")
            for item in comments
            if isinstance(item, dict)
        ):
            return "exists"
        pull = call("GET", f"/repos/{repository}/pulls/{number}")
        merged_at = str(pull.get("merged_at") or "")
        digest = body_digest(pull.get("body"))
        call(
            "POST",
            f"/repos/{repository}/issues/{number}/comments",
            {
                "body": (
                    f"physical-receipt-anchor: pr={number} merge-commit={merge_sha} "
                    f"merged-at={merged_at} body-sha256={digest}\n\n"
                    "Anchor is the merge commit SHA (immutable provider truth). "
                    "`body-sha256` is the sha256 of this pull request's body as the "
                    "provider returned it at merge time, full 64-hex, so a claimed "
                    "digest can be checked against provider bytes by anyone:\n"
                    "`python3 -c 'import hashlib,json,subprocess as s;print("
                    "hashlib.sha256((json.loads(s.check_output([\"gh\",\"api\","
                    f'"repos/{repository}/pulls/{number}"]))["body"] or "")'
                    ".encode()).hexdigest())'`\n"
                    "The Drive index is appended by the periodic batch reconcile; "
                    "receipts are N-class, never a landing-gate dependency."
                )
            },
        )
        return "posted"
    except (SystemExit, Exception):
        return "failed"


def patch_issue(
    repository: str, issue: int, payload: dict[str, Any], call: Any = None
) -> str:
    """Stamp and close the Issue; re-read a refusal before believing it.

    Returns 'applied' when the provider accepted, 'misreported' when it refused
    an effect the readback shows it performed. Re-raises the provider's own
    refusal when the readback shows it did NOT perform it.

    `api()` turns every non-2xx into a `SystemExit`, which is right for a
    request that did nothing and wrong for one that did everything: PR 140's
    PATCH answered 422 with an empty `errors` array and the write had landed --
    body stamped, state closed, timeline recording the close in the same
    second. Nothing here explains why; the claim is only that a provider's
    answer about its own effect is a hypothesis and the readback is the fact.

    The comparison is against what was SENT, not against "looks plausible": a
    422 that genuinely did not apply leaves the issue disagreeing with the
    payload, and that still fails the run.
    """
    call = api if call is None else call
    try:
        call("PATCH", f"/repos/{repository}/issues/{issue}", payload)
        return "applied"
    except SystemExit:
        after = call("GET", f"/repos/{repository}/issues/{issue}")
        if any(after.get(field) != value for field, value in payload.items()):
            raise
        return "misreported"


def main(argv: list[str] | None = None, call: Any = None) -> int:
    call = api if call is None else call
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("policy/github.json"))
    parser.add_argument(
        "--resume",
        action="store_true",
        help="the merge already happened: re-enter the steps after it instead "
        "of exiting PULL_NOT_OPEN. The receipt still names the head, and the "
        "merge is asserted rather than assumed.",
    )
    args = parser.parse_args(argv)

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    policy = json.loads(args.policy.read_text(encoding="utf-8"))

    repository = policy["repository"]
    if receipt.get("repository") != repository:
        raise SystemExit(f"RECEIPT_FOREIGN_REPOSITORY:{receipt.get('repository')}")
    number = int(receipt["pull_request"])
    head = receipt["head_sha"]

    pull = call("GET", f"/repos/{repository}/pulls/{number}")
    # Identity before state: `--resume` must be as exact about WHICH tree it is
    # finishing as the first attempt was about which tree it merged.
    if pull["head"]["sha"] != head:
        raise SystemExit(f"HEAD_MOVED:{number}:{pull['head']['sha']}:{head}")
    if pull["base"]["ref"] != policy["default_branch"]:
        raise SystemExit(f"BASE_NOT_DEFAULT_BRANCH:{number}:{pull['base']['ref']}")
    issue = parse_refs(pull.get("body"), repository)

    if args.resume:
        # Re-entry, not a second merge: the provider's own `merged` flag is the
        # only thing that may supply the merge commit here.
        if not pull.get("merged"):
            raise SystemExit(f"RESUME_NOT_MERGED:{number}:{pull['state']}")
        merge_sha = pull["merge_commit_sha"]
    else:
        if pull["state"] != "open":
            raise SystemExit(f"PULL_NOT_OPEN:{number}:{pull['state']}")
        merged = call(
            "PUT",
            f"/repos/{repository}/pulls/{number}/merge",
            {"sha": head, "merge_method": policy["merge_method"]},
        )
        if not merged.get("merged"):
            raise SystemExit(f"MERGE_REFUSED:{number}:{merged.get('message')}")
        merge_sha = merged["sha"]

        readback = call("GET", f"/repos/{repository}/pulls/{number}")
        if not readback.get("merged"):
            raise SystemExit(f"MERGE_READBACK_ABSENT:{number}")

    # Before the Issue PATCH, not after the closure readback: the merge is
    # irreversible and this is the only artifact that makes it checkable by a
    # third party, so it must not sit behind a step that can fail.
    anchor = post_receipt_anchor(repository, number, merge_sha, call=call)

    body = call("GET", f"/repos/{repository}/issues/{issue}").get("body")
    patched = patch_issue(
        repository,
        issue,
        {
            "body": stamp(
                body,
                {
                    "state": "landed",
                    "landed-pr": f"{repository}#{number}",
                    "head": head,
                    "merge": merge_sha,
                },
            ),
            "state": "closed",
            "state_reason": "completed",
        },
        call=call,
    )
    closed = call("GET", f"/repos/{repository}/issues/{issue}")
    if closed["state"] != "closed":
        raise SystemExit(f"ISSUE_CLOSE_READBACK_ABSENT:{issue}:{closed['state']}")

    print(
        json.dumps(
            {
                "landed_pull_request": number,
                "head_sha": head,
                "merge_sha": merge_sha,
                "closed_issue": issue,
                "issue_patch": patched,
                "receipt_anchor": anchor,
                "resumed": args.resume,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if patched == "applied" else PROVIDER_MISREPORTED


if __name__ == "__main__":
    raise SystemExit(main())
