"""Planted falsifiers for the land gate's two pure decisions."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from land_pr import parse_refs, stamp  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
