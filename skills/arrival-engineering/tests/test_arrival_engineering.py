"""Hermetic falsifiers for the arrival-engineering bundle.

Positive controls prove the live bundle and both selftests are green; the
negative controls each hollow one side of a tie and require the validator to
red. A tie nobody has watched break is a sentence, not a gate.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import audit_islands  # noqa: E402
import gen_receipts  # noqa: E402
import validate_arrival_engineering as validator  # noqa: E402


def load_fixture(name: str) -> tuple[Path, dict, Path]:
    tree = SKILL_ROOT / "evals" / "fixtures" / name
    path = tree / "capabilities.json"
    return tree, json.loads(path.read_text(encoding="utf-8")), path


class ArrivalEngineeringEvals(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = Path(tempfile.mkdtemp(prefix="arrival-tests-"))
        self.addCleanup(shutil.rmtree, self.scratch, True)

    def copy(self) -> Path:
        target = self.scratch / f"copy{len(list(self.scratch.iterdir()))}"
        shutil.copytree(
            SKILL_ROOT, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
        return target

    def edit(self, path: Path, old: str, new: str) -> None:
        """Replace every occurrence, then assert the anchor is really gone.

        A markdown link carries its target twice (label and href); a
        replace-first would leave the second copy and quietly turn a negative
        control into a test that proves nothing.
        """
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"anchor absent in {path}")
        replaced = text.replace(old, new)
        self.assertNotIn(old, replaced, f"anchor survived the edit in {path}")
        path.write_text(replaced, encoding="utf-8")

    # ---------------------------------------------------------------- positive

    def test_live_bundle_passes_every_tie(self) -> None:
        self.assertEqual(validator.validate(SKILL_ROOT, REPO_ROOT), [])

    def test_island_audit_selftest_passes(self) -> None:
        self.assertEqual(audit_islands.selftest(), 0)

    def test_validator_selftest_passes(self) -> None:
        self.assertEqual(validator.selftest(), 0)

    def test_planted_fixtures_produce_every_island_class(self) -> None:
        tree, topology, path = load_fixture("planted")
        report = audit_islands.audit(tree, topology, path)
        seen = {item["diagnostic"] for item in report["findings"]}
        expected = set(audit_islands.DIAGNOSTICS) - {"TOPOLOGY_ROW_WITHOUT_RECEIPT"}
        self.assertEqual(seen, expected)
        self.assertTrue(report["read_only"]["held"])

    def test_negative_controls_are_not_flagged(self) -> None:
        tree, topology, path = load_fixture("clean")
        report = audit_islands.audit(tree, topology, path)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["outcome"], "clean")

    def test_gen_receipts_is_idempotent_and_authors_the_committed_bytes(self) -> None:
        topology = json.loads(
            (SKILL_ROOT / "domain" / "capability-topology.json").read_text(encoding="utf-8")
        )
        rendered = gen_receipts.render(topology)
        self.assertEqual(
            (SKILL_ROOT / "receipts.json").read_text(encoding="utf-8"), rendered
        )
        self.assertEqual(gen_receipts.render(topology), rendered)

    # ---------------------------------------------------------------- negative

    def test_append_without_receipt_is_refused(self) -> None:
        tree, topology, _ = load_fixture("clean")
        with self.assertRaises(audit_islands.AppendRefused) as raised:
            audit_islands.append_row(
                topology,
                {"id": "aspirational", "capability": "someday", "arrival": "PRODUCTION"},
                tree,
            )
        self.assertIn("TOPOLOGY_ROW_WITHOUT_RECEIPT:aspirational", str(raised.exception))

    def test_dropping_a_kernel_entry_fails(self) -> None:
        copy = self.copy()
        path = copy / "references" / "portable-arrival-kernel.md"
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        path.write_text(
            "".join(line for line in lines if not line.startswith("- K6 ")), encoding="utf-8"
        )
        self.assertTrue(
            any("count mismatch" in error for error in validator.validate(copy, REPO_ROOT))
        )

    def test_hand_edited_receipts_fail(self) -> None:
        copy = self.copy()
        path = copy / "receipts.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["evidence"]["closure-by-pointer"]["claim"] = "a nicer sentence"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "not what gen_receipts.py produces" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_claim_above_arrival_fails(self) -> None:
        copy = self.copy()
        path = copy / "domain" / "capability-topology.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        for row in body["rows"]:
            if row["id"] == "noodles-where-is-x-slice":
                row["arrival"] = "PRODUCTION"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any("CLAIM_ABOVE_ARRIVAL" in error for error in validator.validate(copy, REPO_ROOT))
        )

    def test_claim_below_arrival_fails(self) -> None:
        """An understated row reds too, or the ledger is only author memory.

        The over-claim direction was always caught. This one is the direction
        that made a permanently-stale row invisible: nothing ever noticed a row
        whose receipts had outgrown it.
        """
        copy = self.copy()
        path = copy / "domain" / "capability-topology.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        for row in body["rows"]:
            if row["id"] == "sc-spatial-loop-grounded-checks":
                row["arrival"] = "DECLARED"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any("CLAIM_BELOW_ARRIVAL" in error for error in validator.validate(copy, REPO_ROOT))
        )

    def test_a6_restating_the_owner_laws_fails(self) -> None:
        copy = self.copy()
        self.edit(
            copy / "SKILL.md",
            validator.CLOSURE_OWNER,
            "notes/our-own-copy-of-the-laws.md",
        )
        self.assertTrue(
            any(
                "does not point at the closure law" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_undocumented_diagnostic_fails(self) -> None:
        copy = self.copy()
        self.edit(copy / "SKILL.md", "`DOCUMENTED_PIN_FALSE`", "DOCUMENTED_PIN_FALSE")
        self.assertTrue(
            any(
                "Diagnostics section omits a diagnostic" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_self_announcing_negative_arm_fails(self) -> None:
        copy = self.copy()
        path = copy / "evals" / "behavioral-campaigns" / "judge-inputs" / "r-c3" / "chore.txt"
        path.write_text(
            path.read_text(encoding="utf-8") + "\n(this one is the negative control)\n",
            encoding="utf-8",
        )
        self.assertTrue(
            any("announces itself" in error for error in validator.validate(copy, REPO_ROOT))
        )

    def test_undefined_arrival_level_fails(self) -> None:
        copy = self.copy()
        self.edit(copy / "SKILL.md", "**EXERCISED**", "EXERCISED")
        self.assertTrue(
            any(
                "arrival level EXERCISED is not defined" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )


if __name__ == "__main__":
    unittest.main()
