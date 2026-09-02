"""Eval harness for control-backup: positive controls + hollow mutations.

Every mutation models a way the three-layer skill could silently degrade; each
must FAIL the validator (or the L2 driver selftest). This is the hillclimb gate.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import gen_backup_receipts  # noqa: E402
from validate_control_backup import validate  # noqa: E402


def mutated_copy() -> tuple[tempfile.TemporaryDirectory, Path]:
    temp = tempfile.TemporaryDirectory(prefix="ctlbk-eval-")
    root = Path(temp.name) / "skill"
    shutil.copytree(SKILL_ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
    return temp, root


class ControlBackupEvals(unittest.TestCase):
    def test_positive_control_passes(self) -> None:
        self.assertEqual(validate(SKILL_ROOT), [])

    def test_l2_driver_selftest_passes(self) -> None:
        r = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "backup_driver.py"), "--selftest"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_layer_file_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        (root / "references" / "portable-backup-policy.md").unlink()
        self.assertTrue(any("L-layer" in e or "L0" in e for e in validate(root)), validate(root))

    def test_unbacked_receipt_removed_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        p = root / "receipts.json"
        d = json.loads(p.read_text())
        d["evidence"].pop("freeze-then-replicate-verified")
        p.write_text(json.dumps(d))
        self.assertTrue(any("freeze-then-replicate-verified" in e for e in validate(root)), validate(root))

    def test_openrsync_admitted_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        p = root / "domain" / "backup-topology.json"
        d = json.loads(p.read_text())
        d["not_admitted"].pop("openrsync")
        p.write_text(json.dumps(d))
        self.assertTrue(any("openrsync" in e for e in validate(root)), validate(root))

    def test_driver_negative_control_defused_fails(self) -> None:
        # If someone weakens a driver assertion so a negative control no longer
        # goes red, the selftest (and thus validate) must fail.
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        drv = root / "scripts" / "backup_driver.py"
        t = drv.read_text()
        # defuse: make the churn-tolerance class accept every exit code
        t = t.replace("rc in (0, 24)", "True")
        drv.write_text(t)
        self.assertTrue(any("selftest" in e for e in validate(root)), validate(root))

    # ------------------------------------------------------------------
    # The producer field's author, ed3c/skill-concerns#84. These fields were
    # right and hand-written; what is asserted here is that they are now a
    # function of an execution, and that the function refuses rather than
    # guesses. A generator that only ever ran against a conformant file has
    # never refused anything.

    def committed(self) -> dict:
        return json.loads((SKILL_ROOT / "receipts.json").read_text(encoding="utf-8"))

    def test_the_committed_receipts_are_what_the_producer_makes(self) -> None:
        # The positive arm, through a real driver run: every stamped producer
        # is a claim some assertion replayed green moments ago.
        results = gen_backup_receipts.run_driver()
        self.assertEqual(
            (SKILL_ROOT / "receipts.json").read_text(encoding="utf-8"),
            gen_backup_receipts.render(self.committed(), results),
        )

    def test_a_receipt_naming_an_assertion_that_does_not_exist_is_refused(self) -> None:
        results = gen_backup_receipts.run_driver()
        results.pop("lock_takeover")
        with self.assertRaises(gen_backup_receipts.ReceiptRefused) as caught:
            gen_backup_receipts.build(self.committed(), results)
        self.assertIn("RECEIPT_ASSERTION_ABSENT:single-writer-race", str(caught.exception))

    def test_a_receipt_whose_assertion_reds_is_refused(self) -> None:
        results = gen_backup_receipts.run_driver()
        results["lock_takeover"] = False
        with self.assertRaises(gen_backup_receipts.ReceiptRefused) as caught:
            gen_backup_receipts.build(self.committed(), results)
        self.assertIn("RECEIPT_ASSERTION_RED:single-writer-race", str(caught.exception))

    def test_an_entry_claiming_the_driver_with_no_correspondence_is_refused(self) -> None:
        # The exact shape #84 names: a producer field typed by hand for a claim
        # nothing replays. HOST_OBSERVED is the earned default, and this is the
        # refusal that keeps it from being an escape hatch in reverse.
        document = self.committed()
        document["evidence"]["exfat-no-hardlink"]["producer"] = gen_backup_receipts.DRIVER
        with self.assertRaises(gen_backup_receipts.ReceiptRefused) as caught:
            gen_backup_receipts.build(document, gen_backup_receipts.run_driver())
        self.assertIn("RECEIPT_PRODUCER_UNEARNED:exfat-no-hardlink", str(caught.exception))

    def test_a_hand_edited_receipts_file_reds_the_validator(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "receipts.json"
        document = json.loads(path.read_text())
        document["evidence"]["exfat-no-unix-socket"]["producer"] = "scripts/backup_driver.py"
        path.write_text(json.dumps(document, indent=2) + "\n")
        self.assertTrue(
            any("RECEIPT_PRODUCER_UNEARNED" in e for e in validate(root)), validate(root)
        )


if __name__ == "__main__":
    unittest.main()
