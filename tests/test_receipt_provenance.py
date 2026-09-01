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

import check_admissions  # noqa: E402
import check_receipt_provenance  # noqa: E402
from common import digest_entries, regular_files, sha256_file, tree_digest  # noqa: E402

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
        temp = tempfile.TemporaryDirectory(prefix="receipt-provenance-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name) / "repo"
        shutil.copytree(
            ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        # Both gates take an already-resolved root from their own `main()`.
        return root.resolve()

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


if __name__ == "__main__":
    unittest.main()
