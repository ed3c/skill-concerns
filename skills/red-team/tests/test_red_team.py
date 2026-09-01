"""Hermetic falsifiers for the red-team bundle.

Positive controls prove the live bundle, the historical boundary run, and the
handoff round trip. The negative controls each hollow one side of a tie, or
plant one defect, and require the validator or the driver to red. A tie nobody
has watched break is a sentence, not a gate.
"""

from __future__ import annotations

import hashlib
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
import gen_receipts  # noqa: E402
import shadow_driver as driver  # noqa: E402
import validate_red_team as validator  # noqa: E402

FIXTURES = SKILL_ROOT / "evals" / "fixtures"
WAVE_17 = FIXTURES / "wave-17"
CLEAN = FIXTURES / "clean"
TEMPLATE = FIXTURES / "issue-round-trip" / "body-template.md"


def catalogue() -> dict:
    return json.loads((SKILL_ROOT / "domain" / "catalogue.json").read_text(encoding="utf-8"))


class RedTeamEvals(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = Path(tempfile.mkdtemp(prefix="red-team-tests-"))
        self.addCleanup(shutil.rmtree, self.scratch, True)

    def copy(self) -> Path:
        target = self.scratch / f"copy{len(list(self.scratch.iterdir()))}"
        shutil.copytree(
            SKILL_ROOT, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
        return target

    # ---------------------------------------------------------------- positive

    def test_live_bundle_passes_every_tie(self) -> None:
        self.assertEqual(validator.validate(SKILL_ROOT, REPO_ROOT), [])

    def test_validator_selftest_passes(self) -> None:
        self.assertEqual(validator.selftest(), 0)

    def test_boundary_run_reproduces_the_known_findings(self) -> None:
        """Catalogue plus toolkit alone, with no dispatcher rule text at all.

        The two the admission issue names are the all-exit gate vacuity and one
        blind-observer case; the run reproduces both without being told what to
        look for beyond the pinned bytes.
        """
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        found = {finding["catalogue_class"] for finding in report["findings"]}
        self.assertIn("free-exit", found)
        self.assertIn("blind-observer", found)
        self.assertEqual(report["outcome"], "changed")
        self.assertTrue(report["read_only"]["held"])
        for finding in report["findings"]:
            with self.subTest(finding=finding["id"]):
                self.assertEqual([], validator.finding_errors(finding))

    def test_a_clean_bundle_produces_no_findings(self) -> None:
        """The planted negative control, and it is not vacuous.

        The clean bundle carries an artifact of every kind the wave-17 bundle
        carries - a lane report making an absence claim through a demonstrated
        observer, a grounded receipts file, a frozen anchor, an authorized
        enforcement shape - so "no findings" is a measurement rather than an
        empty directory.
        """
        report = driver.run(CLEAN, catalogue(), "wave-18", "admission-fixture")
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["outcome"], "clean")
        for kind in driver.ARTIFACT_KINDS:
            with self.subTest(kind=kind):
                self.assertTrue(driver.bundle_files(CLEAN, kind))

    def test_a_gated_class_leaves_active_sampling_but_keeps_its_experiment(self) -> None:
        """Graduation, both halves.

        `shape-copying` gated when ed3c/skill-concerns#93 landed. It must drop
        out of sampling - and its experiment must still find the instance when
        called directly, or the lifecycle field would be indistinguishable from
        a broken detector.
        """
        self.assertNotIn("shape-copying", driver.sampled_classes(catalogue()))
        self.assertTrue(driver.EXPERIMENTS["shape-copying"](WAVE_17))
        self.assertEqual([], driver.EXPERIMENTS["shape-copying"](CLEAN))

    def test_the_committed_run_record_is_what_the_fixture_run_produces(self) -> None:
        """The ledger's one record is derived, not typed."""
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        produced = driver.ledger_record(report)
        ledger = json.loads(
            (SKILL_ROOT / "domain" / "run-ledger.json").read_text(encoding="utf-8")
        )
        committed = dict(ledger["records"][0])
        produced.pop("run_id")
        committed.pop("run_id")
        self.assertEqual(committed, produced)

    def test_the_finding_block_drops_into_an_issue_body_and_passes_the_dry_run(self) -> None:
        """The round trip: finding -> body template -> admission completeness."""
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        block = driver.render_demonstration(report["findings"][0])
        body = TEMPLATE.read_text(encoding="utf-8").replace("{demonstration}", block)
        self.assertEqual([], validator.completeness_reasons(body))
        self.assertIn(block, body)

    def test_gen_receipts_is_idempotent_and_authors_the_committed_bytes(self) -> None:
        rendered = gen_receipts.render(catalogue())
        self.assertEqual(
            (SKILL_ROOT / "receipts.json").read_text(encoding="utf-8"), rendered
        )
        self.assertEqual(gen_receipts.render(catalogue()), rendered)

    def test_an_adjudicated_class_folds_in(self) -> None:
        """The planted negative control for the BUILD refusal below."""
        entry = {
            "id": "planted-adjudicated-class",
            "cure_authorization": dict(cure_authorization.ADJUDICATED_AUTHORIZATION),
        }
        grown = driver.add_class(catalogue(), entry)
        self.assertEqual(len(grown["classes"]), len(catalogue()["classes"]) + 1)

    # ---------------------------------------------------------------- negative

    def test_an_unadjudicated_class_cannot_legislate_the_catalogue(self) -> None:
        """BUILD fold-in behind the landed ed3c/skill-concerns#93 gate.

        A catalogue class IS an enforcement shape, so the authorization is not
        conditional on the words the entry happens to use.
        """
        with self.assertRaises(driver.BuildRefused) as raised:
            driver.add_class(catalogue(), {"id": "planted-unadjudicated-class"})
        self.assertIn(cure_authorization.DIAGNOSTIC, str(raised.exception))

    def test_a_shadow_detection_never_legislates_the_catalogue(self) -> None:
        with self.assertRaises(driver.BuildRefused) as raised:
            driver.add_class(
                catalogue(),
                {
                    "id": "planted-detected-class",
                    "cure_authorization": {
                        "kind": "shadow-detection",
                        "ref": "ed3c/skill-concerns#94",
                    },
                },
            )
        self.assertIn("SHADOW detections never authorize", str(raised.exception))

    def test_a_malformed_finding_fails_the_validator(self) -> None:
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        good = report["findings"][0]
        blank = {**good, "experiment": {**good["experiment"], "observed": "  "}}
        self.assertTrue(any("no observed" in e for e in validator.finding_errors(blank)))
        prose = {
            **good,
            "experiment": {**good["experiment"], "commands": ["look at the receipts file"]},
        }
        self.assertTrue(
            any("prose where a command belongs" in e for e in validator.finding_errors(prose))
        )

    def test_a_fenced_demonstration_block_fails_the_admission_dry_run(self) -> None:
        """Why the grammar has no fence, proven rather than asserted.

        The consumer's gate strips fenced blocks before it decides whether a
        section carries an authored assertion, so the identical content inside
        a fence arrives there as an empty section.
        """
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        block = driver.render_demonstration(report["findings"][0])
        fenced = TEMPLATE.read_text(encoding="utf-8").replace(
            "{demonstration}", f"```\n{block}\n```"
        )
        self.assertTrue(
            any("Observer demonstration" in reason for reason in validator.completeness_reasons(fenced))
        )

    def test_a_signal_outside_the_urgent_list_is_a_validator_error(self) -> None:
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        with self.assertRaises(ValueError) as raised:
            driver.escalate(report["findings"][0], "S2", "the exit is free")
        self.assertIn("outside the bounded", str(raised.exception))
        signal = driver.escalate(
            {**report["findings"][0], "catalogue_class": validator.URGENT_CLASSES[0]},
            "S2",
            "a force-push is in flight against a protected ref",
        )
        self.assertEqual([], validator.signal_errors(signal))

    def test_a_provider_mutating_call_in_the_driver_reds_the_scan(self) -> None:
        copy = self.copy()
        path = copy / "scripts" / "shadow_driver.py"
        path.write_text(
            path.read_text(encoding="utf-8")
            + '\n\ndef file_it(number: int) -> None:\n'
            '    subprocess.run(["gh", "issue", "create", "--title", str(number)])\n',
            encoding="utf-8",
        )
        self.assertTrue(
            any("DRIVER_SURFACE_FORBIDDEN" in error for error in validator.validate(copy, REPO_ROOT))
        )

    def test_a_gated_class_without_a_gate_reference_fails(self) -> None:
        copy = self.copy()
        path = copy / "domain" / "catalogue.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        for entry in body["classes"]:
            if entry["status"] == "gated":
                entry["gate_ref"] = None
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "CATALOGUE_GATE_REFERENCE_ABSENT" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_a_class_without_provenance_or_recipe_fails(self) -> None:
        copy = self.copy()
        path = copy / "domain" / "catalogue.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["classes"][0].pop("provenance")
        body["classes"][1]["falsification"]["recipe"] = ["read it carefully"]
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        errors = validator.validate(copy, REPO_ROOT)
        self.assertTrue(any("no provenance receipt grounds" in error for error in errors))
        self.assertTrue(
            any("not a runnable command sequence" in error for error in errors)
        )

    def test_dropping_a_kernel_entry_fails(self) -> None:
        copy = self.copy()
        path = copy / "references" / "portable-falsification-kernel.md"
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        path.write_text(
            "".join(line for line in lines if not line.startswith("- K7 ")),
            encoding="utf-8",
        )
        self.assertTrue(any("count mismatch" in error for error in validator.validate(copy, REPO_ROOT)))

    def test_hand_edited_receipts_fail(self) -> None:
        copy = self.copy()
        path = copy / "receipts.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["evidence"]["blind-observer"]["claim"] = "a nicer sentence"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "not what gen_receipts.py produces" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_a_subject_that_moved_during_the_pass_refuses_its_own_report(self) -> None:
        """Reader-only by measurement. The plant mutates the bundle mid-pass."""
        bundle = self.scratch / "bundle"
        shutil.copytree(WAVE_17, bundle)
        original = driver.experiment_free_exit

        def writes_to_the_subject(target: Path):
            (target / "reports" / "PLANTED_MONITOR_WRITE.txt").write_text(
                "a monitor must never write here\n", encoding="utf-8"
            )
            return original(target)

        driver.EXPERIMENTS["free-exit"] = writes_to_the_subject
        try:
            report = driver.run(bundle, catalogue(), "wave-17", "admission-fixture")
        finally:
            driver.EXPERIMENTS["free-exit"] = original
        self.assertEqual(report["outcome"], "blocked")
        self.assertFalse(report["read_only"]["held"])
        self.assertEqual(report["findings"], [])

    def test_a_flat_curve_after_three_waves_is_itself_a_finding(self) -> None:
        flat = {
            "records": [
                {"wave": f"wave-{index}", "hits": {"blind-observer": 2}}
                for index in (17, 18, 19)
            ]
        }
        self.assertIn("CURVE_NOT_DECLINING", driver.curve_finding(flat))
        bending = {
            "records": [
                {"wave": "wave-17", "hits": {"blind-observer": 3}},
                {"wave": "wave-18", "hits": {"blind-observer": 2}},
                {"wave": "wave-19", "hits": {"blind-observer": 1}},
            ]
        }
        self.assertIsNone(driver.curve_finding(bending))
        self.assertIsNone(driver.curve_finding({"records": flat["records"][:2]}))

    def test_a_flat_curve_leaves_through_the_exit_code(self) -> None:
        """R7 is a finding, so it does not exit 0 as stdout prose.

        A finding that leaves the process at status 0 is consumed by nobody:
        the caller that would act on it reads the exit code. The run itself is
        clean here, so a non-zero status can only have come from the curve.
        """
        ledger = self.scratch / "ledger.json"
        ledger.write_text(
            json.dumps(
                {
                    "records": [
                        {
                            "run_id": f"2026-08-{day:02d}T00:00:00+00:00",
                            "wave": f"wave-{day}",
                            "boundary": "b",
                            "classes_sampled": [],
                            "hits": {},
                            "novel_class_candidates": [],
                            "judge_gaps": 0,
                            "duplicate_blocks": 0,
                        }
                        for day in (10, 11)
                    ]
                }
            ),
            encoding="utf-8",
        )
        status = driver.main(
            [
                "--bundle", str(CLEAN),
                "--wave", "wave-12",
                "--ledger", str(ledger),
                "--append-record",
            ]
        )
        self.assertEqual(
            "clean",
            driver.run(CLEAN, catalogue(), "wave-12", "stage-close")["outcome"],
        )
        self.assertNotEqual(0, status)

    def test_every_recipe_runs_through_the_drivers_own_parser(self) -> None:
        """A recipe naming a flag the driver has not got is not runnable.

        `COMMAND_RE` certifies that a step LOOKS like a command; only the real
        parser certifies that it runs. Both directions: the live catalogue's
        recipes parse, and a planted unknown flag reds.
        """
        errors: list[str] = []
        validator.check_recipes_parse(catalogue(), errors)
        self.assertEqual([], errors)

        copy = self.copy()
        path = copy / "domain" / "catalogue.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["classes"][0]["falsification"]["recipe"] = [
            "python3 scripts/shadow_driver.py --bundle <bundle> --klass blind-observer"
        ]
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "--klass" in error and "does not accept" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_a_method_claim_without_an_authorization_is_refused(self) -> None:
        """The exemption is gone: method claims name who adjudicated them."""
        copy = self.copy()
        path = copy / "domain" / "catalogue.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        for claim in body["method_claims"].values():
            claim.pop("authorization")
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                cure_authorization.DIAGNOSTIC in error
                and "names who adjudicated it" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_a_hand_typed_run_id_reds_the_ledger(self) -> None:
        """`run_id` is the producer's clock, and a label is not a clock."""
        copy = self.copy()
        path = copy / "domain" / "run-ledger.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["records"][0]["run_id"] = "the wave-17 admission run"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "is not the producer's ISO-8601 instant" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_a_bundle_script_that_could_spawn_a_process_reds(self) -> None:
        """Reader-only covers every script, not only the one named in the test.

        The verb scan cannot cover its own owner, which necessarily holds the
        verbs; this is the property underneath it, and it covers all five.
        """
        copy = self.copy()
        path = copy / "scripts" / "gen_receipts.py"
        path.write_text(
            "import subprocess\n" + path.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.assertTrue(
            any(
                "DRIVER_SURFACE_FORBIDDEN:gen_receipts.py" in error
                and "spawn a process" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_the_absent_neighbour_exit_re_resolves_when_the_absence_ends(self) -> None:
        """The exit expires by landed state, not by anyone remembering it."""
        fake_repo = self.scratch / "repo"
        for name in (*validator.NEIGHBOURS, validator.ABSENT_NEIGHBOUR):
            (fake_repo / "skills" / name).mkdir(parents=True)
        self.assertTrue(
            any(
                "has landed in this tree" in error
                for error in validator.validate(SKILL_ROOT, fake_repo)
            )
        )

    def test_a_duplicate_finding_binds_the_digest_of_the_file_it_names(self) -> None:
        """The subject digest is the file at subject.path, or it binds nothing.

        A monitor whose contract is digest-binding publishing a digest of its
        own fingerprint string would put an unverifiable hex into every issue
        the dispatcher files from a duplicate-discovery finding.
        """
        hits = driver.EXPERIMENTS["duplicate-discovery"](WAVE_17)
        self.assertTrue(hits)
        for hit in hits:
            subject = hit["subject"]
            expected = hashlib.sha256(
                (WAVE_17 / subject["path"]).read_bytes()
            ).hexdigest()
            self.assertEqual(expected, subject["sha256"])

    def test_unchanged_context_cannot_acquit_an_added_enforcement_shape(self) -> None:
        """Detection and acquittal read the same bytes.

        Detecting on added lines while acquitting on the whole patch lets a
        diff be exculpated by a word it did not add - including the word
        `falsification`, which every catalogue entry contains.
        """
        bundle = self.scratch / "context-acquittal"
        (bundle / "diffs").mkdir(parents=True)
        (bundle / "diffs" / "planted.diff").write_text(
            "--- a/limits.json\n"
            "+++ b/limits.json\n"
            "@@ -1,3 +1,4 @@\n"
            ' {\n'
            '   "note": "see the falsification recipe in the catalogue",\n'
            '+  "threshold": 36,\n'
            '   "owner": "fitness"\n',
            encoding="utf-8",
        )
        self.assertTrue(driver.EXPERIMENTS["shape-copying"](bundle))


if __name__ == "__main__":
    unittest.main()
