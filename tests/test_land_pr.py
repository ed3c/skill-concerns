"""Planted falsifiers for the land gate's two pure decisions."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from land_pr import parse_refs, post_receipt_anchor, stamp  # noqa: E402


REPOSITORY = "ed3c/skill-concerns"


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
                return {"merged_at": "2026-09-01T00:00:00Z"}
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


if __name__ == "__main__":
    unittest.main()
