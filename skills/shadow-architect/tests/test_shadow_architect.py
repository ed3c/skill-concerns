#!/usr/bin/env python3
"""Falsifiers for the shadow-architect bundle.

Every FAIL case in `evals/cases.json` has its own assertion here. A negative arm
that shares its producer with a positive one is one execution counted twice, so
the arms below never point at the same method.

The planted-mutation suite -- hollow one side of a tie, assert the validator
reds -- is NOT re-authored here. `validate_shadow_architect.selftest()` owns it,
`test_validator_selftest_passes` runs every one of its checks on each
invocation, and a second copy of the same mutations would be that one execution
counted twice with two places to keep in step.
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
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import cure_authorization  # noqa: E402
import gen_shadow_receipts  # noqa: E402
import precedent_driver as driver  # noqa: E402
import validate_shadow_architect as validator  # noqa: E402

FIXTURES = SKILL_ROOT / "evals" / "fixtures"
WAVE_17 = FIXTURES / "waves" / "wave-17-bootstrap-entry-fields.diff"
PLANTED = FIXTURES / "planted" / "over-designed.diff"
CLEAN = FIXTURES / "planted" / "clean.diff"
KEY = FIXTURES / "planted" / "ANSWER-KEY.md"

# The two findings the wave-17 monitor record names, by the bytes it quoted.
# Read back from the record itself rather than paraphrased here: the ledger
# carries them in each clause's `reproduces` field and the validator ties that
# field to what the driver actually quotes.
KNOWN_WAVE_17_CLAUSES = ("P1", "P2")


def ledger() -> dict:
    return driver.load_ledger(SKILL_ROOT)


def clauses(report: dict) -> set[str]:
    return {record["clause"] for record in report["findings"]}


def answer_key_clauses(heading: str) -> set[str]:
    """The clauses the key says an arm must raise, parsed from its table.

    Read only here, after the run. The driver takes one diff path and opens
    that path only, and `ANSWER_KEY_VISIBLE` refuses any script in the bundle
    that names this file, so the blindness is structural rather than promised.
    """
    body = KEY.read_text(encoding="utf-8").split(f"## `{heading}`", 1)[1]
    body = body.split("\n## ", 1)[0]
    return {
        cell.strip().strip("`")
        for line in body.splitlines()
        if line.startswith("| `P")
        for cell in [line.split("|")[1]]
    }


class ShadowArchitectEvals(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = Path(tempfile.mkdtemp(prefix="shadow-architect-test-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)

    def copy(self) -> Path:
        target = self.scratch / "bundle"
        shutil.copytree(
            SKILL_ROOT, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
        return target

    def edit_ledger(self, bundle: Path, change) -> None:
        path = bundle / "domain" / "precedents.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        change(body)
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- PASS

    def test_live_bundle_passes_every_tie(self) -> None:
        self.assertEqual([], validator.validate(SKILL_ROOT, REPO_ROOT))

    def test_validator_selftest_passes(self) -> None:
        self.assertEqual(0, validator.selftest())

    def test_the_historical_wave_diff_reproduces_the_known_findings(self) -> None:
        """The acceptance run: one real wave diff, the findings that wave made.

        Reproduced from the pinned ledger and the driver alone - no fixture
        carries an expected report, so a green here is the detectors reading
        the real bytes rather than a recorded answer being echoed.
        """
        report = driver.run(WAVE_17, ledger())
        self.assertEqual("changed", report["outcome"])
        raised = clauses(report)
        for clause in KNOWN_WAVE_17_CLAUSES:
            self.assertIn(clause, raised)
        quoted = {
            item["bytes"]
            for record in report["findings"]
            for item in record["quoted"]
        }
        entries = {entry["id"]: entry for entry in ledger()["precedents"]}
        for clause in KNOWN_WAVE_17_CLAUSES:
            for needle in entries[clause]["reproduces"]:
                self.assertTrue(
                    any(needle in line for line in quoted),
                    f"{clause} did not quote the bytes its monitor record quoted",
                )

    def test_every_clause_fires_on_its_fixture_and_is_silent_on_its_control(self) -> None:
        for precedent in ledger()["precedents"]:
            with self.subTest(clause=precedent["id"]):
                fixture = (SKILL_ROOT / precedent["fixture"]).read_text(encoding="utf-8")
                self.assertTrue(driver.match(precedent, fixture))
                control = (SKILL_ROOT / precedent["control"]).read_text(encoding="utf-8")
                self.assertEqual([], driver.match(precedent, control))

    def test_every_provenance_binds_the_commit_its_fixture_carries(self) -> None:
        for precedent in ledger()["precedents"]:
            with self.subTest(clause=precedent["id"]):
                provenance = precedent["provenance"]
                fixture = (SKILL_ROOT / precedent["fixture"]).read_text(encoding="utf-8")
                self.assertIn(provenance["subject_commit"], fixture)
                self.assertTrue(provenance["wave_receipt"])

    def test_the_planted_over_designed_arm_raises_exactly_the_key(self) -> None:
        report = driver.run(PLANTED, ledger())
        self.assertEqual(
            answer_key_clauses("over-designed.diff"), clauses(report)
        )

    def test_the_planted_clean_arm_raises_nothing(self) -> None:
        report = driver.run(CLEAN, ledger())
        self.assertEqual("clean", report["outcome"])
        self.assertEqual(set(), clauses(report))

    def test_the_campaign_is_blind_by_construction(self) -> None:
        """No script can see the key, and the pass opens one path only."""
        for script in sorted((SKILL_ROOT / "scripts").glob("*.py")):
            if script.name == validator.ANSWER_KEY_EXEMPT:
                continue
            with self.subTest(script=script.name):
                self.assertNotIn(
                    validator.ANSWER_KEY_TOKEN, script.read_text(encoding="utf-8")
                )
        parser = driver.build_parser()
        args = parser.parse_args(["--diff", str(CLEAN)])
        self.assertEqual(CLEAN, args.diff)

    def test_gen_shadow_receipts_is_idempotent_and_authors_the_committed_bytes(self) -> None:
        once = gen_shadow_receipts.render(ledger())
        self.assertEqual(once, gen_shadow_receipts.render(ledger()))
        self.assertEqual(
            (SKILL_ROOT / "receipts.json").read_text(encoding="utf-8"), once
        )

    def test_an_adjudicated_precedent_folds_in(self) -> None:
        """The planted negative control's positive arm."""
        folded = driver.fold_in(
            ledger(),
            {
                "id": "P8",
                "title": "a planted but adjudicated precedent",
                "provenance": {
                    "wave_receipt": ["ed3c/skill-concerns#75"],
                    "quote": "a monitor record that says what the wave found",
                },
                "cure_authorization": {
                    "kind": "discriminating-measurement",
                    "ref": "ed3c/skill-concerns#75",
                },
            },
        )
        self.assertEqual("P8", folded["precedents"][-1]["id"])
        self.assertEqual(7, len(ledger()["precedents"]), "fold_in is pure")

    def test_a_severity_rises_when_one_shape_repeats_across_files(self) -> None:
        """S2 has a producer rather than a field an author sets.

        Both arms, in one measurement: the same clause in one file is a warning,
        and the same clause in two files is a review, because a shape repeated
        across files is architecture rather than an accident.
        """
        precedent = next(entry for entry in ledger()["precedents"] if entry["id"] == "P3")
        one_file = (
            "+++ b/scripts/a.py\n"
            "@@ -1,1 +1,2 @@\n"
            '+HEX40 = re.compile(r"^[0-9a-f]{40}$")\n'
        )
        two_files = one_file + (
            "+++ b/scripts/b.py\n"
            "@@ -1,1 +1,2 @@\n"
            '+HEX40 = re.compile(r"^[0-9a-f]{40}$")\n'
        )
        subject = {"path": "planted.diff", "sha256": "0" * 64}
        warned = driver.finding(precedent, subject, driver.match(precedent, one_file))
        reviewed = driver.finding(precedent, subject, driver.match(precedent, two_files))
        self.assertEqual(driver.WARN, warned["severity"])
        self.assertEqual(driver.REVIEW, reviewed["severity"])

    # ---------------------------------------------------------------- FAIL

    def test_an_adjudicated_precedent_with_no_receipt_is_still_refused(self) -> None:
        with self.assertRaises(driver.BuildRefused) as raised:
            driver.fold_in(
                ledger(),
                {
                    "id": "planted-ungrounded-clause",
                    "cure_authorization": {
                        "kind": "discriminating-measurement",
                        "ref": "ed3c/skill-concerns#75",
                    },
                },
            )
        self.assertIn("PRECEDENT_WITHOUT_PROVENANCE", str(raised.exception))

    def test_a_subject_that_moved_during_the_pass_refuses_its_own_report(self) -> None:
        subject = self.scratch / "moving.diff"
        shutil.copyfile(WAVE_17, subject)
        original = driver.digest

        def moving(path: Path) -> str:
            value = original(path)
            if path == subject:
                path.write_text(
                    path.read_text(encoding="utf-8") + "\n+ planted\n", encoding="utf-8"
                )
            return value

        driver.digest = moving
        try:
            report = driver.run(subject, ledger())
        finally:
            driver.digest = original
        self.assertEqual("blocked", report["outcome"])
        self.assertEqual([], report["findings"])
        self.assertIn("SUBJECT_MUTATED", report["refusal"])

    def test_unchanged_context_cannot_acquit_an_added_shape(self) -> None:
        """Acquittal reads added lines only, or any nearby comment silences it."""
        precedent = next(
            entry for entry in ledger()["precedents"] if entry["id"] == "P2"
        )
        diff = (
            "+++ b/scripts/thing.py\n"
            "@@ -1,2 +1,3 @@\n"
            " # this module uses posixpath.normpath elsewhere\n"
            '+    if part.startswith(f"skills/{name}/"):\n'
        )
        self.assertTrue(driver.match(precedent, diff))
        acquitted = diff + "+    part = posixpath.normpath(part)\n"
        self.assertEqual([], driver.match(precedent, acquitted))

    def test_one_files_acquittal_does_not_clear_another_file(self) -> None:
        """An exculpation is a claim about the file that carries it.

        Pooled over the diff, any one file's incantation - including this
        bundle's own ledger travelling in the same landing, which spells every
        acquittal literal verbatim - would silence the clause everywhere the
        diff reaches.
        """
        precedent = next(
            entry for entry in ledger()["precedents"] if entry["id"] == "P2"
        )
        cured = (
            "+++ b/scripts/cured.py\n"
            "@@ -1,1 +1,2 @@\n"
            '+    if posixpath.normpath(part).startswith(f"skills/{name}/"):\n'
        )
        raw = (
            "+++ b/scripts/raw.py\n"
            "@@ -1,1 +1,2 @@\n"
            '+    if part.startswith(f"skills/{name}/"):\n'
        )
        self.assertEqual(
            ["scripts/raw.py"],
            [path for path, _, _ in driver.match(precedent, cured + raw)],
        )


if __name__ == "__main__":
    unittest.main()
