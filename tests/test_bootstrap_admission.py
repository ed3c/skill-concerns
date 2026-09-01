"""A first-ever admission needs a trusted way in that is not a skeleton key.

`SKILL_CHECKS` is imported from the validator's own tree (`admission_stamp.py`
imports it at module scope; `check_receipt_provenance` re-executes through it),
so a candidate can never declare the checks that grade it. The cost is that the
first commit to add a Skill is also the first commit to add its row, and the
gate reads that row from a branch the commit is not on yet: PR 68 died on
`ADMISSION_STAMP_REFUSED:dynamic-workflow:NO_DECLARED_CHECKS`
(ed3c/skill-concerns#72).

`admission_stamp.BOOTSTRAP` is the way in. These falsifiers plant the four
states that separate it from a skeleton key:

  positive   authorized bytes reproduce their committed receipt with no
             `SKILL_CHECKS` row anywhere;
  negative   bytes the entry did not authorize refuse before executing;
  negative   no entry keeps the original diagnostic verbatim, so "unauthorized"
             and "authorized and green" never share a shape;
  negative   a pending entry is green only while the Skill it names is absent,
             and an entry that outlives the landing it bought reds the tree.

The trusted copy is proved to be the one that counts by deleting the graded
tree's copy first: every green below is produced with no allowlist inside the
tree being weighed.

No control here names a shipped entry. Entries are transient by construction --
each is deleted by the landing it authorizes -- so a control that asserted the
presence of one would turn `main` red on the day that landing succeeded, which
is the opposite of what it is for. The pending states are planted instead, and
the committed allowlist is checked only for the properties that hold both while
it carries an entry and after it carries none.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import admission_stamp  # noqa: E402
import check_admissions  # noqa: E402
import check_receipt_provenance  # noqa: E402
from admission_stamp import REFUSAL  # noqa: E402
from common import digest_entries, regular_files, tree_digest  # noqa: E402
from run_all import SKILL_CHECKS  # noqa: E402

# Stand-in for a Skill arriving for the first time: an admitted bundle whose
# `SKILL_CHECKS` row is withdrawn for the duration of a test, which is exactly
# the tree state a first-admission candidate presents to the trusted gate. Its
# committed receipt is the oracle -- a bootstrapped execution must reproduce
# the same bytes the ordinary row produces, or the two paths are not the same
# admission.
SUBJECT = "control-backup"

# A Skill name no tree here carries, so the pending and spent states can be
# planted without depending on which admission happens to be in flight.
PLANTED = "bootstrap-subject"

ALLOWLIST = "policy/bootstrap-admissions.json"


class BootstrapAdmissionTests(unittest.TestCase):
    def scratch_copy(self) -> Path:
        temp = tempfile.TemporaryDirectory(prefix="bootstrap-admission-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name) / "repo"
        shutil.copytree(
            ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        # Every gate takes an already-resolved root from its own `main()`.
        return root.resolve()

    def trusted_tree(self) -> Path:
        """A directory standing in for CI's `.trusted` checkout."""
        temp = tempfile.TemporaryDirectory(prefix="bootstrap-trusted-")
        self.addCleanup(temp.cleanup)
        return Path(temp.name)

    def digest(self, root: Path, skill: str) -> str:
        return tree_digest(digest_entries(root, regular_files(root / "skills" / skill)))

    def authorize(self, path: Path, skill: str, digest: str, **overrides: object) -> Path:
        entry: dict[str, object] = {
            "skill": skill,
            "refs": "ed3c/skill-concerns#72",
            "authorized_head": "0" * 40,
            "skill_tree_sha256": digest,
            "checks": [list(argv) for argv in SKILL_CHECKS.get(skill, ())],
        }
        entry.update(overrides)
        path.write_text(
            json.dumps({"schema_version": 1, "entries": [entry]}, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def plant_pending(self, root: Path) -> Path:
        """Replace `root`'s allowlist with one entry for a Skill it does not have."""
        path = self.authorize(
            root / ALLOWLIST,
            PLANTED,
            "a" * 64,
            checks=[[f"skills/{PLANTED}/scripts/validate_{PLANTED}.py"]],
        )
        self.assertFalse((root / "skills" / PLANTED).exists())
        return path

    def first_admission(self, root: Path, skill: str, allowlist: Path):
        """Withdraw `skill`'s row and point the trusted read at `allowlist`.

        The graded tree's own allowlist is deleted, so nothing below can pass
        by reading the candidate's copy of its own authorization.
        """
        (root / ALLOWLIST).unlink(missing_ok=True)
        withdrawn = {
            name: argv for name, argv in SKILL_CHECKS.items() if name != skill
        }
        return mock.patch.multiple(
            admission_stamp, SKILL_CHECKS=withdrawn, BOOTSTRAP=allowlist
        )

    def test_authorized_first_admission_reproduces_its_committed_receipt(self) -> None:
        """The planted positive: no row anywhere, and the gate still re-executes."""
        root = self.scratch_copy()
        committed = (root / "admissions" / f"{SUBJECT}.json").read_bytes()
        allowlist = self.authorize(
            self.trusted_tree() / "bootstrap-admissions.json",
            SUBJECT,
            self.digest(root, SUBJECT),
        )

        with self.first_admission(root, SUBJECT, allowlist):
            self.assertNotIn(SUBJECT, admission_stamp.SKILL_CHECKS)
            self.assertFalse((root / ALLOWLIST).exists())
            self.assertEqual([], check_receipt_provenance.check(root, only={SUBJECT}))

        self.assertEqual(
            committed,
            (root / "admissions" / f"{SUBJECT}.json").read_bytes(),
            "a bootstrapped admission must reproduce the same receipt, not a new one",
        )

    def test_bytes_the_entry_did_not_authorize_refuse_before_executing(self) -> None:
        """The digest binds the reviewed tree, not the name on the entry."""
        root = self.scratch_copy()
        allowlist = self.authorize(
            self.trusted_tree() / "bootstrap-admissions.json",
            SUBJECT,
            self.digest(root, SUBJECT),
        )

        readme = root / "skills" / SUBJECT / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8") + "\none line the reviewer never saw\n",
            encoding="utf-8",
        )

        with self.first_admission(root, SUBJECT, allowlist):
            errors = check_receipt_provenance.check(root, only={SUBJECT})

        self.assertEqual(1, len(errors), errors)
        self.assertTrue(
            errors[0].startswith(f"{REFUSAL}:{SUBJECT}:BOOTSTRAP_DIGEST_MISMATCH:"),
            errors,
        )
        self.assertIn(
            self.digest(root, SUBJECT),
            errors[0],
            "the refusal must name the digest the candidate actually has",
        )

    def test_an_unauthorized_first_admission_keeps_the_verbatim_refusal(self) -> None:
        """Absence stays the diagnostic PR 68 got, in both shapes of absence."""
        root = self.scratch_copy()
        trusted = self.trusted_tree()
        expected = [f"{REFUSAL}:{SUBJECT}:NO_DECLARED_CHECKS"]

        with self.first_admission(root, SUBJECT, trusted / "absent.json"):
            self.assertEqual(
                expected,
                check_receipt_provenance.check(root, only={SUBJECT}),
                "no allowlist at all",
            )

        other = self.authorize(
            trusted / "other.json", PLANTED, "f" * 64, checks=[[f"skills/{PLANTED}/x.py"]]
        )
        with self.first_admission(root, SUBJECT, other):
            self.assertEqual(
                expected,
                check_receipt_provenance.check(root, only={SUBJECT}),
                "an allowlist that authorizes some other Skill",
            )

    def test_a_rejected_allowlist_refuses_rather_than_reading_as_unauthorized(
        self,
    ) -> None:
        """A malformed entry must not decay into the silent 'no entry' shape."""
        root = self.scratch_copy()
        trusted = self.trusted_tree()
        planted = {
            "BOOTSTRAP_ENTRY_DIGEST_INVALID": {"skill_tree_sha256": "not-a-digest"},
            "BOOTSTRAP_ENTRY_ARGV_FOREIGN": {
                "checks": [["skills/some-other-skill/scripts/validate.py"]]
            },
            "BOOTSTRAP_ENTRY_REFS_INVALID": {"refs": "trust me"},
        }
        for diagnostic, override in planted.items():
            with self.subTest(diagnostic=diagnostic):
                allowlist = self.authorize(
                    trusted / f"{diagnostic}.json",
                    SUBJECT,
                    self.digest(root, SUBJECT),
                    **override,
                )
                _, errors = admission_stamp.bootstrap_entries(allowlist)
                self.assertTrue(
                    any(error.startswith(diagnostic) for error in errors), errors
                )
                with mock.patch.object(admission_stamp, "BOOTSTRAP", allowlist):
                    with self.assertRaises(admission_stamp.StampRefused) as refusal:
                        admission_stamp.bootstrap_checks(SUBJECT, root)
                self.assertIn("BOOTSTRAP_FILE_REJECTED", str(refusal.exception))

    def test_a_pending_entry_is_green_while_its_skill_is_absent(self) -> None:
        """The state `main` sits in between the two landings."""
        root = self.scratch_copy()
        self.plant_pending(root)
        self.assertEqual([], check_admissions.check(root))
        self.assertNotIn(
            PLANTED, SKILL_CHECKS, "a pending entry is not a landed row"
        )

    def test_an_entry_that_outlives_its_landing_reds_the_tree(self) -> None:
        """Consumed or retired: the landing commit must delete its own entry."""
        root = self.scratch_copy()
        self.plant_pending(root)

        (root / "skills" / PLANTED).mkdir()
        self.assertIn(
            f"BOOTSTRAP_ENTRY_STALE:{PLANTED}",
            check_admissions.check(root),
            "an authorization left standing after its Skill landed",
        )

        (root / ALLOWLIST).unlink()
        self.assertEqual(
            [],
            check_admissions.check(root),
            "retiring the entry is what makes the landed tree green",
        )

    def test_the_committed_allowlist_carries_only_pending_authorizations(self) -> None:
        """True with an admission in flight and true with none in flight.

        Every entry this tree ships must parse, must name a Skill that has not
        arrived, and must not duplicate a landed `SKILL_CHECKS` row -- the
        three properties that distinguish an authorization still owed from one
        already spent. An empty allowlist satisfies all three honestly.
        """
        entries, errors = admission_stamp.bootstrap_entries(admission_stamp.BOOTSTRAP)
        self.assertEqual([], errors)
        for skill in entries:
            with self.subTest(skill=skill):
                self.assertFalse((ROOT / "skills" / skill).exists())
                self.assertNotIn(skill, SKILL_CHECKS)
        self.assertEqual([], check_admissions.check(ROOT))


if __name__ == "__main__":
    unittest.main()
