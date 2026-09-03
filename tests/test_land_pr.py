"""Planted falsifiers for the land gate's pure decisions and its sequence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import land_pr  # noqa: E402
from common import HEX64  # noqa: E402
from land_pr import (  # noqa: E402
    PROVIDER_MISREPORTED,
    body_digest,
    main,
    parse_refs,
    patch_issue,
    post_receipt_anchor,
    stamp,
)


REPOSITORY = "ed3c/skill-concerns"

# The fixture body: a real PR body's shape - marker comments, a Refs line, and
# the CRLF the provider actually returns - so the digest under test is taken
# over bytes with something to normalise away, and nothing does.
PR_BODY = "Refs ed3c/skill-concerns#77\r\n\r\n<!-- noodles-role: repository-mutating-atom -->\r\n"
ANCHOR_FIELD = re.compile(r"body-sha256=([0-9a-fA-F]*)")


class RefsLineTests(unittest.TestCase):
    def test_single_line_resolves(self) -> None:
        self.assertEqual(16, parse_refs("Refs ed3c/skill-concerns#16", REPOSITORY))

    def test_absent_line_fails_closed(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            parse_refs("no reference at all", REPOSITORY)
        self.assertEqual("REFS_LINE_COUNT:0", str(caught.exception))

    def test_two_lines_fail_closed(self) -> None:
        body = "Refs ed3c/skill-concerns#16\nRefs ed3c/skill-concerns#11"
        with self.assertRaises(SystemExit) as caught:
            parse_refs(body, REPOSITORY)
        self.assertEqual("REFS_LINE_COUNT:2", str(caught.exception))

    def test_foreign_repository_fails_closed(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            parse_refs("Refs ed3c/noodles#16", REPOSITORY)
        self.assertEqual("REFS_FOREIGN_REPOSITORY:ed3c/noodles", str(caught.exception))


class MarkerStampTests(unittest.TestCase):
    def test_existing_marker_is_replaced_in_place(self) -> None:
        body = (
            "<!-- noodles-role: repository-mutating-atom -->\n"
            "<!-- noodles-state: awaiting_land -->\n"
            "## Goal\n"
        )
        stamped = stamp(body, {"state": "landed"})
        self.assertIn("<!-- noodles-state: landed -->", stamped)
        self.assertNotIn("awaiting_land", stamped)
        self.assertIn("<!-- noodles-role: repository-mutating-atom -->", stamped)
        self.assertIn("## Goal", stamped)

    def test_absent_markers_are_appended_without_losing_content(self) -> None:
        stamped = stamp("## Goal\n", {"head": "a" * 40, "merge": "b" * 40})
        self.assertIn("## Goal", stamped)
        self.assertTrue(stamped.rstrip().endswith(f"<!-- noodles-merge: {'b' * 40} -->"))
        self.assertIn(f"<!-- noodles-head: {'a' * 40} -->", stamped)

    def test_stamp_is_idempotent(self) -> None:
        once = stamp("## Goal\n", {"state": "landed"})
        self.assertEqual(once, stamp(once, {"state": "landed"}))


class ReceiptAnchorTests(unittest.TestCase):
    """The anchor is N-class: once per PR, and it can never gate a land."""

    def test_clean_pr_gets_exactly_one_anchor_comment(self) -> None:
        calls: list[tuple[str, str]] = []

        def fake(method: str, path: str, payload: dict | None = None):
            calls.append((method, path))
            if method == "GET" and "comments" in path:
                return [{"body": "ordinary review comment"}]
            if method == "GET":
                return {"merged_at": "2026-09-01T00:00:00Z", "body": PR_BODY}
            self.assertIn("physical-receipt-anchor: pr=31 merge-commit=" + "c" * 40, payload["body"])
            self.assertIn("merged-at=2026-09-01T00:00:00Z", payload["body"])
            return {}

        self.assertEqual("posted", post_receipt_anchor(REPOSITORY, 31, "c" * 40, call=fake))
        self.assertEqual(1, sum(1 for method, _ in calls if method == "POST"))

    def test_existing_anchor_is_never_duplicated(self) -> None:
        def fake(method: str, path: str, payload: dict | None = None):
            if method == "GET" and "comments" in path:
                return [{"body": "physical-receipt-anchor: pr=31 merge-commit=old"}]
            raise AssertionError(f"unexpected call after existing anchor: {method} {path}")

        self.assertEqual("exists", post_receipt_anchor(REPOSITORY, 31, "c" * 40, call=fake))

    def test_provider_refusal_never_gates_the_land(self) -> None:
        # planted negative: the exact failure this anchor exists to dodge
        # (secondary rate limit surfacing as an api() SystemExit) must not raise.
        def fake(method: str, path: str, payload: dict | None = None):
            raise SystemExit("GITHUB_API_REFUSED:POST:/comments:403:secondary rate limit")

        self.assertEqual("failed", post_receipt_anchor(REPOSITORY, 31, "c" * 40, call=fake))


class BodyDigestAnchorTests(unittest.TestCase):
    """The ledger's one mechanical arrival, ed3c/skill-concerns#77.

    Before this the body-digest ledger was self-report all the way down: every
    lane computed its own digests and no machine ever recomputed one. These
    assertions are about the recomputation, not about the lanes.
    """

    def posted_anchor(self, body: str | None) -> str:
        captured: list[str] = []

        def fake(method: str, path: str, payload: dict | None = None):
            if method == "GET" and "comments" in path:
                return []
            if method == "GET":
                return {"merged_at": "2026-09-01T00:00:00Z", "body": body}
            captured.append(payload["body"])
            return {}

        self.assertEqual("posted", post_receipt_anchor(REPOSITORY, 77, "d" * 40, call=fake))
        return captured[0]

    def test_the_anchor_digest_equals_an_independent_recomputation(self) -> None:
        # Independent: hashlib against the fixture bytes, not land_pr's helper.
        expected = hashlib.sha256(PR_BODY.encode("utf-8")).hexdigest()
        recorded = ANCHOR_FIELD.search(self.posted_anchor(PR_BODY)).group(1)
        self.assertEqual(expected, recorded)

    def test_the_recorded_digest_is_full_64_hex(self) -> None:
        recorded = ANCHOR_FIELD.search(self.posted_anchor(PR_BODY)).group(1)
        self.assertRegex(recorded, HEX64)

    def test_a_disagreeing_anchor_is_detectable_by_the_documented_check(self) -> None:
        # The planted control: an anchor recorded against one body, checked
        # against the body the provider actually holds. One character of drift
        # in a 4-line body must be enough; a digest that survived it would be
        # measuring something other than the body.
        recorded = ANCHOR_FIELD.search(self.posted_anchor(PR_BODY)).group(1)
        tampered = PR_BODY.replace("#77", "#78")
        self.assertNotEqual(recorded, body_digest(tampered))
        self.assertEqual(recorded, body_digest(PR_BODY))

    def test_an_absent_body_still_yields_a_digest_rather_than_a_blank(self) -> None:
        # `body` is nullable at the provider. ABSENT must not read as a missing
        # or empty field, which a consumer would have to guess about.
        recorded = ANCHOR_FIELD.search(self.posted_anchor(None)).group(1)
        self.assertRegex(recorded, HEX64)
        self.assertEqual(hashlib.sha256(b"").hexdigest(), recorded)

    def test_the_existing_anchor_fields_are_appended_to_not_reshaped(self) -> None:
        anchor = self.posted_anchor(PR_BODY)
        self.assertIn(f"physical-receipt-anchor: pr=77 merge-commit={'d' * 40}", anchor)
        self.assertIn("merged-at=2026-09-01T00:00:00Z", anchor)
        self.assertLess(anchor.index("merged-at="), anchor.index("body-sha256="))



# ed3c/skill-concerns#141: the recorded shape of PR 140, the one anchorless
# merged pull request this repository has. Its body is the single `Refs` line,
# its issue is 81, and it had zero comments when the landing ended.
PULL = 140
ISSUE = 81
PULL_BODY = f"Refs {REPOSITORY}#{ISSUE}"
HEAD_SHA = "2" * 40
MERGE_SHA = "4" * 40
MERGED_AT = "2026-09-02T20:55:11Z"
COMMENTS_PATH = f"/repos/{REPOSITORY}/issues/{PULL}/comments"
ISSUE_PATH = f"/repos/{REPOSITORY}/issues/{ISSUE}"
REFUSAL_422 = (
    'GITHUB_API_REFUSED:PATCH:{path}:422:{{"message":"Validation Failed",'
    '"errors":[],"status":"422"}}'
)


class Provider:
    """A stubbed provider that can be wrong about its own effect.

    The four dials are the four states the real one produced: whether the pull
    request is already merged, whether the issue PATCH refuses, whether that
    refusal nevertheless applies, and what comments already exist.
    """

    def __init__(
        self,
        *,
        merged: bool = False,
        refuses_patch: bool = False,
        patch_applies: bool = True,
        comments: list[dict] | None = None,
        issue_body: str = "## Goal\n",
        issue_state: str = "open",
        issue_state_reason: str | None = None,
    ) -> None:
        self.merged = merged
        self.refuses_patch = refuses_patch
        self.patch_applies = patch_applies
        self.comments = [] if comments is None else list(comments)
        self.issue = {
            "body": issue_body,
            "state": issue_state,
            "state_reason": issue_state_reason,
        }
        self.calls: list[tuple[str, str]] = []

    def __call__(self, method: str, path: str, payload: dict | None = None):
        self.calls.append((method, path))
        if method == "PUT" and path.endswith("/merge"):
            self.merged = True
            return {"merged": True, "sha": MERGE_SHA}
        if path.startswith(COMMENTS_PATH):
            if method == "POST":
                self.comments.append({"body": payload["body"]})
                return {}
            return list(self.comments)
        if path.startswith(f"/repos/{REPOSITORY}/pulls/"):
            return {
                "merged": self.merged,
                "merge_commit_sha": MERGE_SHA if self.merged else None,
                "state": "closed" if self.merged else "open",
                "head": {"sha": HEAD_SHA},
                "base": {"ref": "main"},
                "body": PULL_BODY,
                "merged_at": MERGED_AT if self.merged else None,
            }
        if method == "GET":
            return dict(self.issue)
        if self.patch_applies:
            self.issue.update(payload)
        if self.refuses_patch:
            raise SystemExit(REFUSAL_422.format(path=path))
        return {}

    def anchors(self) -> list[str]:
        return [
            item["body"]
            for item in self.comments
            if "physical-receipt-anchor" in item["body"]
        ]


class SequenceTestCase(unittest.TestCase):
    def run_land(self, provider: Provider, *extra: str) -> int:
        temp = tempfile.TemporaryDirectory(prefix="land-pr-")
        self.addCleanup(temp.cleanup)
        receipt = Path(temp.name) / "receipt.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "repository": REPOSITORY,
                    "pull_request": PULL,
                    "head_sha": HEAD_SHA,
                }
            ),
            encoding="utf-8",
        )
        argv = ["--receipt", str(receipt), "--policy", str(ROOT / "policy/github.json")]
        return main([*argv, *extra], call=provider)


class MisreportedPatchTests(SequenceTestCase):
    """ed3c/skill-concerns#141: a 422 that already applied is not a failure.

    PR 140 merged, closed and stamped its issue, and the PATCH that did all of
    that answered 422 with an empty `errors` array. `api()` raised, which took
    out the two steps after it, and the merged pull request ended with no
    anchor - the one artifact a third party can recompute the landing from.
    """

    def test_a_refusal_that_applied_reads_back_as_misreported(self) -> None:
        provider = Provider(refuses_patch=True, patch_applies=True)
        self.assertEqual(
            "misreported",
            patch_issue(REPOSITORY, ISSUE, {"state": "closed"}, call=provider),
        )

    def test_a_refusal_that_did_not_apply_still_raises_the_providers_reason(self) -> None:
        # Planted negative. Absence and unreachability must not share a shape:
        # a 422 that changed nothing is a refusal and stays fatal.
        provider = Provider(refuses_patch=True, patch_applies=False)
        with self.assertRaises(SystemExit) as caught:
            patch_issue(REPOSITORY, ISSUE, {"state": "closed"}, call=provider)
        self.assertEqual(REFUSAL_422.format(path=ISSUE_PATH), str(caught.exception))

    def test_the_landing_still_ends_with_an_anchor(self) -> None:
        # The planted control the issue asks for: the provider misreports and
        # the anchor is written anyway, because it no longer sits behind the
        # step that refuses.
        provider = Provider(refuses_patch=True, patch_applies=True)
        self.assertEqual(PROVIDER_MISREPORTED, self.run_land(provider))
        self.assertEqual(1, len(provider.anchors()), provider.comments)
        self.assertIn(f"merge-commit={MERGE_SHA}", provider.anchors()[0])
        self.assertIn("<!-- noodles-state: landed -->", provider.issue["body"])
        self.assertEqual("closed", provider.issue["state"])

    def test_the_anchor_is_written_before_anything_that_can_refuse(self) -> None:
        # Ordering is the cure, not the retry: whatever the issue PATCH answers,
        # the anchor is already posted when it is asked.
        provider = Provider()
        self.assertEqual(0, self.run_land(provider))
        self.assertLess(
            provider.calls.index(("POST", COMMENTS_PATH)),
            provider.calls.index(("PATCH", ISSUE_PATH)),
            provider.calls,
        )

    def test_a_refused_and_unapplied_patch_still_fails_the_run(self) -> None:
        provider = Provider(refuses_patch=True, patch_applies=False)
        with self.assertRaises(SystemExit) as caught:
            self.run_land(provider)
        self.assertIn("GITHUB_API_REFUSED:PATCH:", str(caught.exception))
        # And the anchor is still there: the landing is real either way, so the
        # merged pull request is checkable even when the run exits red.
        self.assertEqual(1, len(provider.anchors()), provider.comments)


class ResumeAfterMergeTests(SequenceTestCase):
    """The recorded PR 140 shape, replayed through the path that backfills it.

    Merged pull request, zero comments, issue already closed and stamped by the
    PATCH that answered 422. Without `--resume` this is `PULL_NOT_OPEN:140` and
    the anchor stays unreachable by the mechanism that produces it.
    """

    def landed_issue_body(self) -> str:
        return stamp(
            "## Goal\n",
            {
                "state": "landed",
                "landed-pr": f"{REPOSITORY}#{PULL}",
                "head": HEAD_SHA,
                "merge": MERGE_SHA,
            },
        )

    def recorded(self) -> Provider:
        return Provider(
            merged=True,
            comments=[],
            issue_body=self.landed_issue_body(),
            issue_state="closed",
            issue_state_reason="completed",
        )

    def test_without_resume_the_anchor_is_unreachable(self) -> None:
        provider = self.recorded()
        with self.assertRaises(SystemExit) as caught:
            self.run_land(provider)
        self.assertEqual(f"PULL_NOT_OPEN:{PULL}:closed", str(caught.exception))
        self.assertEqual([], provider.anchors())

    def test_resume_backfills_the_anchor_and_never_merges_again(self) -> None:
        provider = self.recorded()
        self.assertEqual(0, self.run_land(provider, "--resume"))
        self.assertEqual(1, len(provider.anchors()), provider.comments)
        self.assertIn(f"pr={PULL} merge-commit={MERGE_SHA}", provider.anchors()[0])
        self.assertEqual([], [call for call in provider.calls if call[0] == "PUT"])

    def test_resume_is_idempotent_on_a_pull_that_already_has_one(self) -> None:
        provider = self.recorded()
        self.assertEqual(0, self.run_land(provider, "--resume"))
        self.assertEqual(0, self.run_land(provider, "--resume"))
        self.assertEqual(1, len(provider.anchors()), provider.comments)

    def test_resume_refuses_a_pull_that_never_merged(self) -> None:
        # Planted negative: `--resume` is re-entry after an irreversible step,
        # never a way to skip it.
        provider = Provider(merged=False)
        with self.assertRaises(SystemExit) as caught:
            self.run_land(provider, "--resume")
        self.assertEqual(f"RESUME_NOT_MERGED:{PULL}:open", str(caught.exception))

    def test_resume_still_refuses_a_head_that_moved(self) -> None:
        provider = self.recorded()
        provider_head = "9" * 40
        original = Provider.__call__

        def moved(self, method, path, payload=None):
            answer = original(self, method, path, payload)
            if isinstance(answer, dict) and "head" in answer:
                answer["head"] = {"sha": provider_head}
            return answer

        self.addCleanup(setattr, Provider, "__call__", original)
        Provider.__call__ = moved
        with self.assertRaises(SystemExit) as caught:
            self.run_land(provider, "--resume")
        self.assertEqual(
            f"HEAD_MOVED:{PULL}:{provider_head}:{HEAD_SHA}", str(caught.exception)
        )

    def test_the_re_entry_tells_landed_apart_from_never_landed(self) -> None:
        """The process that reads the three exits is the re-attempt itself.

        Actions has no tri-state step outcome: `PROVIDER_MISREPORTED` fails the
        job exactly as a refusal does, so "landed, provider misreported" and
        "did not land" are one colour to anything watching the job. They are
        two states to the only thing that runs next, which is this same command
        re-entered with `--resume`, and this is that pair measured rather than
        asserted in prose: a completed landing re-enters without merging again
        and without a second anchor, while a run that never got past the merge
        refuses by name.
        """
        landed = Provider(refuses_patch=True, patch_applies=True)
        self.assertEqual(PROVIDER_MISREPORTED, self.run_land(landed))
        self.assertEqual(PROVIDER_MISREPORTED, self.run_land(landed, "--resume"))
        self.assertEqual(1, len(landed.anchors()), landed.comments)
        self.assertEqual(
            1, len([call for call in landed.calls if call[0] == "PUT"]), landed.calls
        )

        never = Provider(merged=False)
        with self.assertRaises(SystemExit) as caught:
            self.run_land(never, "--resume")
        self.assertEqual(f"RESUME_NOT_MERGED:{PULL}:open", str(caught.exception))
        self.assertEqual([], never.anchors())


class ExitCodeSeparationTests(unittest.TestCase):
    def test_misreported_is_neither_success_nor_a_refusal(self) -> None:
        """Three outcomes, three codes: the report shape is the finding."""
        self.assertNotIn(PROVIDER_MISREPORTED, (0, 1, 2))
        self.assertEqual(PROVIDER_MISREPORTED, land_pr.PROVIDER_MISREPORTED)

    def test_the_re_entry_flag_has_a_caller(self) -> None:
        """`--resume` is passed by the workflow, never typed by a person.

        An option no process resolves is prose, and this one guards the step
        after an irreversible action, so it is the worst possible place for a
        flag that exists only in a docstring. The caller is the job's own
        re-attempt: attempt 1 merges, and every later attempt of the same run
        is by construction a re-entry after the merge may already have
        happened. Read off the directives, never the comments -- a workflow
        that only DESCRIBED passing the flag would otherwise satisfy this.
        """
        text = (ROOT / ".github" / "workflows" / "land.yml").read_text(encoding="utf-8")
        directives = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )
        self.assertIn("--resume", directives)
        self.assertIn("github.run_attempt", directives)
        self.assertIn("scripts/land_pr.py", directives)


if __name__ == "__main__":
    unittest.main()
