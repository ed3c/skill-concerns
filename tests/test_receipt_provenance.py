"""The trusted gate must re-execute, not just re-read.

`check_admissions.py` is the only validator CI runs from the default branch
against a candidate tree, and it never runs a Skill's checks: it compares
digests to files that are present and reads `"state": "PASS"` as a string. The
falsifier below builds exactly the receipt that hole admits -- an assertion
deleted from the tree, every digest recomputed to match, every control row still
PASS, no stamper run -- and requires `check_admissions` to be green on it (the
hole is real) while `check_receipt_provenance` refuses it.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import admission_stamp  # noqa: E402
import check_admissions  # noqa: E402
import check_receipt_provenance  # noqa: E402
from common import digest_entries, regular_files, sha256_file, tree_digest  # noqa: E402

GRADED_BY = check_receipt_provenance.GRADED_BY


def scratch_copy(case: unittest.TestCase) -> Path:
    temp = tempfile.TemporaryDirectory(prefix="receipt-provenance-")
    case.addCleanup(temp.cleanup)
    root = Path(temp.name) / "repo"
    shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    # Both gates take an already-resolved root from their own `main()`.
    return root.resolve()

FORGED_SKILL = "control-backup"
FORGED_CASE_ID = "openrsync-admitted"
FORGED_TEST_FILE = "skills/control-backup/tests/test_control_backup.py"
FORGED_ASSERTION = '''    def test_openrsync_admitted_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        p = root / "domain" / "backup-topology.json"
        d = json.loads(p.read_text())
        d["not_admitted"].pop("openrsync")
        p.write_text(json.dumps(d))
        self.assertTrue(any("openrsync" in e for e in validate(root)), validate(root))

'''


class ReceiptProvenanceTests(unittest.TestCase):
    def scratch_copy(self) -> Path:
        return scratch_copy(self)

    def forge(self, root: Path) -> None:
        """Delete an assertion, then repair the receipt the way a forger must.

        Every digest is recomputed so nothing drifts; the control rows are left
        exactly as committed. This is the receipt a hand-editor produces when
        the honest stamper has already refused.
        """
        source = root / FORGED_TEST_FILE
        text = source.read_text(encoding="utf-8")
        self.assertIn(FORGED_ASSERTION, text)
        source.write_text(text.replace(FORGED_ASSERTION, "", 1), encoding="utf-8")

        receipt_path = root / "admissions" / f"{FORGED_SKILL}.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        subject = digest_entries(root, regular_files(root / "skills" / FORGED_SKILL))
        receipt["subject_files"] = subject
        receipt["skill_tree_sha256"] = tree_digest(subject)
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

        self.assertIn(
            {"id": FORGED_CASE_ID, "state": "PASS"},
            receipt["controls"],
            "the forged receipt must still claim the control it can no longer measure",
        )
        self.assertEqual(
            receipt["source_lock"]["sha256"],
            sha256_file(root / receipt["source_lock"]["path"]),
        )

    def test_hand_edited_pass_is_green_on_digests_and_red_on_re_execution(self) -> None:
        root = self.scratch_copy()
        committed = (root / "admissions" / f"{FORGED_SKILL}.json").read_bytes()
        source = root / FORGED_TEST_FILE
        original = source.read_text(encoding="utf-8")

        self.forge(root)
        self.assertEqual(
            [],
            check_admissions.check(root),
            "the digest gate is supposed to be blind to this -- that is the finding",
        )
        errors = check_receipt_provenance.check(root, only={FORGED_SKILL})
        self.assertTrue(
            any(FORGED_CASE_ID in error for error in errors),
            errors,
        )

        source.write_text(original, encoding="utf-8")
        (root / "admissions" / f"{FORGED_SKILL}.json").write_bytes(committed)
        self.assertEqual([], check_admissions.check(root))
        self.assertEqual([], check_receipt_provenance.check(root, only={FORGED_SKILL}))

    def test_runtime_self_rewrite_cannot_launder_drift_into_the_baseline(self) -> None:
        """A candidate test executes with full write access to the same tree
        `reproduce()` is grading. Corrupt the *committed* receipt out of band
        first (standing in for a tree that drifted from what was reviewed),
        then have the Skill's own producer overwrite that file back to
        whatever `build_receipt()` will independently recompute, from inside
        the very subprocess `run_checks()` launches. If the comparison
        baseline were read after that subprocess runs, the runtime rewrite
        would win and the drift would be invisible.
        """
        root = self.scratch_copy()
        receipt_path = root / "admissions" / f"{FORGED_SKILL}.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["controls"][0]["state"] = "STALE"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

        source = root / FORGED_TEST_FILE
        text = source.read_text(encoding="utf-8")
        anchor = "from __future__ import annotations\n"
        self.assertIn(anchor, text)
        self_rewrite = (
            "import json as _json, sys as _sys\n"
            "from pathlib import Path as _Path\n"
            "_root = _Path(__file__).resolve().parents[3]\n"
            "_sys.path.insert(0, str(_root / 'scripts'))\n"
            "from admission_stamp import control_tests as _ct, build_receipt as _br\n"
            f"_bound = _ct({FORGED_SKILL!r}, _root)\n"
            f"_forged = _json.dumps(_br({FORGED_SKILL!r}, _root, _bound), indent=2) + '\\n'\n"
            f"(_root / 'admissions' / '{FORGED_SKILL}.json').write_text(_forged, encoding='utf-8')\n"
        )
        source.write_text(text.replace(anchor, anchor + self_rewrite, 1), encoding="utf-8")

        errors = check_receipt_provenance.check(root, only={FORGED_SKILL})
        # The injected self-rewrite lives inside skill_root, so it also moves
        # subject_files/skill_tree_sha256 -- the point under test is that
        # `controls` (the field the runtime rewrite specifically targeted) is
        # among the fields correctly reported as drifted, not laundered away.
        self.assertIn(f"RECEIPT_NOT_REPRODUCED:{FORGED_SKILL}:controls", errors, errors)

    def test_a_rewritten_row_alone_is_enough_to_refuse(self) -> None:
        """No tree edit at all: only the receipt is touched."""
        root = self.scratch_copy()
        receipt_path = root / "admissions" / f"{FORGED_SKILL}.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["controls"].append({"id": FORGED_CASE_ID, "state": "PASS"})
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(
            [f"RECEIPT_NOT_REPRODUCED:{FORGED_SKILL}:controls"],
            check_receipt_provenance.check(root, only={FORGED_SKILL}),
        )


class GradedByWideningTests(unittest.TestCase):
    """ed3c/skill-concerns#81, landing one of two: the argv trace is accepted.

    A receipt says which controls were measured and not which argv measured
    them, so a bundle graded through its permanent `run_all.SKILL_CHECKS` row
    and the same bundle graded through a `policy/bootstrap-admissions.json`
    entry produce byte-identical receipts. Emitting the field cannot land in
    the same pull request that teaches the gate to accept it: this gate runs
    from the default branch against the candidate, so the emitting change
    would be graded by a comparison that still demands the old bytes.

    Three arms, because fewer would not separate WIDENED from WAIVED: a
    receipt without the field still reproduces, a receipt naming the argv this
    execution selected reproduces, and a receipt naming any other argv is
    refused by name.
    """

    def write(self, root: Path, skill: str, trace) -> None:
        path = root / "admissions" / f"{skill}.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt[GRADED_BY] = trace
        path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    def test_a_receipt_naming_the_executed_argv_still_reproduces(self) -> None:
        root = scratch_copy(self)
        self.write(
            root,
            FORGED_SKILL,
            [list(argv) for argv in admission_stamp.declared_checks(FORGED_SKILL, root)],
        )
        self.assertEqual([], check_receipt_provenance.check(root, only={FORGED_SKILL}))
        # And no second gate has to move first: the digest gate never enumerated
        # a receipt's keys, so landing two needs exactly this one widening.
        self.assertEqual([], check_admissions.check(root))

    def test_a_trace_naming_other_argv_is_refused_by_name(self) -> None:
        # The planted control the issue asks for: a receipt whose `graded_by`
        # does not match the argv the gate actually executed goes red.
        root = scratch_copy(self)
        self.write(root, FORGED_SKILL, [["scripts/run_all.py"]])
        self.assertEqual(
            [f"RECEIPT_GRADED_BY_MISMATCH:{FORGED_SKILL}"],
            check_receipt_provenance.check(root, only={FORGED_SKILL}),
        )

    def test_a_trace_is_not_a_licence_to_drift_elsewhere(self) -> None:
        """Widening one field must not widen the reproduction around it."""
        root = scratch_copy(self)
        path = root / "admissions" / f"{FORGED_SKILL}.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt[GRADED_BY] = [
            list(argv) for argv in admission_stamp.declared_checks(FORGED_SKILL, root)
        ]
        receipt["controls"].append({"id": FORGED_CASE_ID, "state": "PASS"})
        path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(
            [f"RECEIPT_NOT_REPRODUCED:{FORGED_SKILL}:controls"],
            check_receipt_provenance.check(root, only={FORGED_SKILL}),
        )

    def test_landing_one_moved_no_receipt_data(self) -> None:
        """The property that lets the trusted gate grade this change at all.

        It is also the reader landing two needs: the field is all-or-nothing
        across the committed set, because a half-migrated set would leave it
        permanently optional -- a widening nobody ever narrows.
        """
        receipts = sorted((ROOT / "admissions").glob("*.json"))
        self.assertTrue(receipts)
        carrying = [
            path.name
            for path in receipts
            if GRADED_BY in json.loads(path.read_text(encoding="utf-8"))
        ]
        self.assertIn(len(carrying), (0, len(receipts)), carrying)


if __name__ == "__main__":
    unittest.main()
