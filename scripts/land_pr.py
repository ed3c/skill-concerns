#!/usr/bin/env python3
"""Land a verified pull request at its exact verified head and close its Issue.

Trust split: the receipt (produced by the trusted verify job) names *which*
commit was verified; policy/github.json on the default branch names the
repository, base branch and merge method. Nothing is taken from the candidate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


API = "https://api.github.com"
REFS_LINE = re.compile(r"^Refs\s+([A-Za-z0-9._-]+/[A-Za-z0-9._-]+)#(\d+)$")


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

    N-class: runs only after merge + issue-closure readback and can never gate
    a land - every failure path returns 'failed' instead of raising. The Drive
    index is appended by the periodic batch reconcile, not here.
    Returns 'exists' | 'posted' | 'failed'.
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
        merged_at = str(call("GET", f"/repos/{repository}/pulls/{number}").get("merged_at") or "")
        call(
            "POST",
            f"/repos/{repository}/issues/{number}/comments",
            {
                "body": (
                    f"physical-receipt-anchor: pr={number} merge-commit={merge_sha} "
                    f"merged-at={merged_at}\n\n"
                    "Anchor is the merge commit SHA (immutable provider truth). The Drive "
                    "index is appended by the periodic batch reconcile; receipts are "
                    "N-class, never a landing-gate dependency."
                )
            },
        )
        return "posted"
    except (SystemExit, Exception):
        return "failed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("policy/github.json"))
    args = parser.parse_args(argv)

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    policy = json.loads(args.policy.read_text(encoding="utf-8"))

    repository = policy["repository"]
    if receipt.get("repository") != repository:
        raise SystemExit(f"RECEIPT_FOREIGN_REPOSITORY:{receipt.get('repository')}")
    number = int(receipt["pull_request"])
    head = receipt["head_sha"]

    pull = api("GET", f"/repos/{repository}/pulls/{number}")
    if pull["state"] != "open":
        raise SystemExit(f"PULL_NOT_OPEN:{number}:{pull['state']}")
    if pull["head"]["sha"] != head:
        raise SystemExit(f"HEAD_MOVED:{number}:{pull['head']['sha']}:{head}")
    if pull["base"]["ref"] != policy["default_branch"]:
        raise SystemExit(f"BASE_NOT_DEFAULT_BRANCH:{number}:{pull['base']['ref']}")
    issue = parse_refs(pull.get("body"), repository)

    merged = api(
        "PUT",
        f"/repos/{repository}/pulls/{number}/merge",
        {"sha": head, "merge_method": policy["merge_method"]},
    )
    if not merged.get("merged"):
        raise SystemExit(f"MERGE_REFUSED:{number}:{merged.get('message')}")
    merge_sha = merged["sha"]

    readback = api("GET", f"/repos/{repository}/pulls/{number}")
    if not readback.get("merged"):
        raise SystemExit(f"MERGE_READBACK_ABSENT:{number}")

    body = api("GET", f"/repos/{repository}/issues/{issue}").get("body")
    api(
        "PATCH",
        f"/repos/{repository}/issues/{issue}",
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
    )
    closed = api("GET", f"/repos/{repository}/issues/{issue}")
    if closed["state"] != "closed":
        raise SystemExit(f"ISSUE_CLOSE_READBACK_ABSENT:{issue}:{closed['state']}")

    anchor = post_receipt_anchor(repository, number, merge_sha)

    print(
        json.dumps(
            {
                "landed_pull_request": number,
                "head_sha": head,
                "merge_sha": merge_sha,
                "closed_issue": issue,
                "receipt_anchor": anchor,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
