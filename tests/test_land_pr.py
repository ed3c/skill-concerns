"""Planted falsifiers for the land gate's two pure decisions."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import HEX64  # noqa: E402
from land_pr import body_digest, parse_refs, post_receipt_anchor, stamp  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
