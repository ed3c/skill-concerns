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
import gen_red_team_receipts  # noqa: E402
import shadow_driver as driver  # noqa: E402
import validate_red_team as validator  # noqa: E402

FIXTURES = SKILL_ROOT / "evals" / "fixtures"
WAVE_17 = FIXTURES / "wave-17"
CLEAN = FIXTURES / "clean"
GENERATION_CLOSE = FIXTURES / "generation-close"
YIELDED = FIXTURES / "yielded-non-report"
TEMPLATE = FIXTURES / "issue-round-trip" / "body-template.md"
STATION = "noodles-generation-close"

# The dispatcher's evidence-marker block, and it is an ARGUMENT because upstream
# takes it as one: the values are parsed from the issue's marker block by a
# producer that is not in `issue_contract.py`, so the mirror declines to invent a
# parser for bytes it never read. `none` here is the honest declaration for a
# template whose demonstration is a fixture block and whose acceptance prescribes
# no external tool behavior. A finding that DOES claim an observation owes the
# invocation and two discriminating directions -- ed3c/skill-concerns#148.
HONEST_NONE = {"observer": "none", "capability-probe": "none"}


def catalogue() -> dict:
    return json.loads((SKILL_ROOT / "domain" / "catalogue.json").read_text(encoding="utf-8"))


def domain(name: str) -> dict:
    return json.loads((SKILL_ROOT / "domain" / name).read_text(encoding="utf-8"))


def catalogue_as_of(record: dict) -> dict:
    """The catalogue restricted to the classes one committed record sampled.

    A run record is a measurement taken under the classes in force at its
    instant, and the ledger is append-only. Re-deriving it from whatever the
    catalogue carries NOW is `trusted-current-literal` aimed at this bundle's
    own controls: every landed class would force a rewrite of every historical
    record, which is exactly what an append-only ledger forbids. The record's
    own `classes_sampled` is the pin, and the caller asserts that pin is a
    subset of the live catalogue so a record cannot name a class that never
    existed and be re-derived against it.
    """
    body = catalogue()
    body["classes"] = [
        entry for entry in body["classes"] if entry["id"] in record["classes_sampled"]
    ]
    return body


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

    def test_a_yielded_payload_recorded_as_a_result_is_reported(self) -> None:
        """ed3c/skill-concerns#105, both directions, in one bundle.

        Positive: the short payload that declares itself alive and carries none
        of the report contract's blocks. Negative, two arms, because one is not
        enough to show the conjunction is load-bearing - a full report, and a
        full report that NARRATES a yield it recovered from. A detector that
        fired on the second would refuse every honest account of a
        park-and-resume, which is the false positive this class would otherwise
        buy.
        """
        hits = driver.EXPERIMENTS["yielded-non-report"](YIELDED)
        self.assertEqual(
            ["reports/lane-report-yielded.md"],
            [hit["subject"]["path"] for hit in hits],
        )
        observed = hits[0]["observed"]
        self.assertIn("Still in progress", observed)
        self.assertIn("branch@sha", observed)
        payload = YIELDED / "reports" / "lane-report-yielded.md"
        self.assertIn(f"{len(payload.read_bytes())} bytes", observed)

        for report in ("lane-report-complete.md", "lane-report-recovered.md"):
            with self.subTest(negative=report):
                text = (YIELDED / "reports" / report).read_text(encoding="utf-8")
                for name, pattern in driver.REPORT_CONTRACT_BLOCKS.items():
                    self.assertTrue(pattern.search(text), name)

        self.assertEqual([], driver.EXPERIMENTS["yielded-non-report"](CLEAN))
        self.assertEqual([], driver.EXPERIMENTS["yielded-non-report"](WAVE_17))

    def test_the_yielded_class_only_fires_on_the_conjunction(self) -> None:
        """The planted negative for the second half of the predicate.

        Strip the contract blocks out of the recovered report and it becomes
        the class; leave them in and the same self-declaration is not a
        finding. Measured against a scratch copy, so the fixture keeps both
        arms.
        """
        bundle = self.scratch / "yield-conjunction"
        (bundle / "reports").mkdir(parents=True)
        source = (YIELDED / "reports" / "lane-report-recovered.md").read_text(
            encoding="utf-8"
        )
        target = bundle / "reports" / "lane-report-recovered.md"

        target.write_text(source, encoding="utf-8")
        self.assertEqual([], driver.EXPERIMENTS["yielded-non-report"](bundle))

        stripped = "\n".join(
            line
            for line in source.splitlines()
            if not any(
                pattern.search(line)
                for pattern in driver.REPORT_CONTRACT_BLOCKS.values()
            )
        )
        target.write_text(stripped + "\n", encoding="utf-8")
        self.assertTrue(driver.YIELD_DECLARATION.search(stripped), "the arm is vacuous")
        self.assertEqual(
            ["reports/lane-report-recovered.md"],
            [
                hit["subject"]["path"]
                for hit in driver.EXPERIMENTS["yielded-non-report"](bundle)
            ],
        )

    def test_the_committed_run_record_is_what_the_fixture_run_produces(self) -> None:
        """The ledger's first record is derived, not typed."""
        ledger = json.loads(
            (SKILL_ROOT / "domain" / "run-ledger.json").read_text(encoding="utf-8")
        )
        committed = dict(ledger["records"][0])
        self.assertEqual(
            driver.sampled_classes(catalogue())[: len(committed["classes_sampled"])],
            committed["classes_sampled"],
            "BUILD only ever appends, so the classes in force at a record's "
            "instant are a PREFIX of today's active list; a record that names a "
            "class the catalogue never carried, or that skips one it did, has "
            "been edited rather than measured",
        )
        report = driver.run(
            WAVE_17, catalogue_as_of(committed), "wave-17", "admission-fixture"
        )
        produced = driver.ledger_record(report)
        produced.pop("run_id")
        committed.pop("run_id")
        self.assertEqual(committed, produced)

    def test_the_finding_block_drops_into_an_issue_body_and_passes_the_dry_run(self) -> None:
        """The round trip: finding -> body template -> admission completeness."""
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        block = driver.render_demonstration(report["findings"][0])
        body = TEMPLATE.read_text(encoding="utf-8").replace("{demonstration}", block)
        self.assertEqual([], validator.completeness_reasons(body, HONEST_NONE))
        self.assertIn(block, body)

    def test_an_undeclared_marker_block_fails_closed(self) -> None:
        """ed3c/skill-concerns#137: no declaration is a refusal, never a pass.

        `declared` cannot be read off a body -- upstream takes it as an argument
        too -- so the mirror's default is "nothing declared". A default that
        skipped the evidence half would make this dry run quieter than the gate
        it mirrors, which is the one direction a dry run must never fail in.
        """
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        block = driver.render_demonstration(report["findings"][0])
        body = TEMPLATE.read_text(encoding="utf-8").replace("{demonstration}", block)
        reasons = validator.completeness_reasons(body)
        for marker in ("observer", "capability-probe"):
            self.assertTrue(
                any(f"declares no noodles-{marker} marker" in reason for reason in reasons),
                reasons,
            )

    def test_the_demonstration_is_graded_by_the_reader_that_keeps_fences(self) -> None:
        """The drift ed3c/skill-concerns#137 cures, as a fixture.

        Before ed3c/noodles#317 every reader stripped fences, so this bundle
        concluded a fenced demonstration reached the gate as an empty section and
        shaped `render_demonstration` around it. Upstream now routes exactly that
        section through `sections(body, keep_fences=True)`. Fenced or not, the
        demonstration reader sees the same text -- and the pre-#317 mirror REDS
        this case, which is what makes it a fixture for the drift rather than a
        restatement of the cure.
        """
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        block = driver.render_demonstration(report["findings"][0])
        template = TEMPLATE.read_text(encoding="utf-8")
        plain = template.replace("{demonstration}", block)
        fenced = template.replace("{demonstration}", f"```\n{block}\n```")
        self.assertEqual(
            validator.sections(plain, keep_fences=True)["observer_demonstration"].strip("`\n "),
            validator.sections(fenced, keep_fences=True)["observer_demonstration"].strip("`\n "),
        )
        self.assertEqual([], validator.completeness_reasons(fenced, HONEST_NONE))
        # The reader that still strips is unchanged: the fenced content is gone.
        self.assertEqual("", validator.sections(fenced).get("observer_demonstration", ""))

    def test_a_fenced_required_section_still_reds_the_reader_that_strips(self) -> None:
        """The negative control keeps its subject: the readers that DO strip.

        `observer_demonstration` left the stripping reader; REQUIRED_SECTIONS did
        not. A required section whose only content is a fence still arrives empty
        and is still refused by name.
        """
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        block = driver.render_demonstration(report["findings"][0])
        body = TEMPLATE.read_text(encoding="utf-8").replace("{demonstration}", block)
        goal = validator.sections(body)["goal"]
        fenced_goal = body.replace(goal, f"```\n{goal}\n```")
        self.assertNotEqual(body, fenced_goal)
        reasons = validator.completeness_reasons(fenced_goal, HONEST_NONE)
        # Lowercased because upstream builds the reason from the SECTION KEY, not
        # from the heading it read; the mirror reproduces that verbatim.
        self.assertIn("issue body has no '## goal' section", reasons)

    def test_a_declared_observer_marker_owes_two_discriminating_directions(self) -> None:
        """The evidence half ed3c/noodles#317 added, mirrored and measured.

        Declaring the invocation instead of `none` buys the whole gate: both
        direction labels, the identical invocation inside each, an output under
        it, and outputs that actually differ. The monitor's block records one
        transcript and declares the second direction in prose
        (`falsification.both_directions`), so it cannot satisfy this. That gap is
        ed3c/skill-concerns#148 -- measured here, not papered over here.
        """
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        finding = report["findings"][0]
        invocation = finding["experiment"]["commands"][0]
        template = TEMPLATE.read_text(encoding="utf-8")
        declared = {"observer": invocation, "capability-probe": "none"}

        block = driver.render_demonstration(finding)
        reasons = validator.completeness_reasons(
            template.replace("{demonstration}", block), declared
        )
        for label in ("GREEN", "RED"):
            self.assertTrue(
                any(f"carries no {label} direction" in reason for reason in reasons), reasons
            )

        def transcript(green: str, red: str) -> str:
            return (
                f"GREEN (clean subject)\n\n{invocation}\n{green}\n\n"
                f"RED (planted violation)\n\n{invocation}\n{red}\n"
            )

        self.assertEqual(
            [],
            validator.completeness_reasons(
                template.replace("{demonstration}", transcript("0", "3")), declared
            ),
        )
        identical = validator.completeness_reasons(
            template.replace("{demonstration}", transcript("0", "0")), declared
        )
        self.assertTrue(
            any("did not discriminate" in reason for reason in identical), identical
        )

    def test_every_blind_probe_is_disposed_not_merely_labelled(self) -> None:
        """ed3c/skill-concerns#83: the refusal names where to look instead.

        A blind surface that is only labelled leaves the next lane to re-derive
        the substitute, and re-deriving it is how this probe reached every lane
        of five waves. The sighted surface must be named, must read the editor
        logins (counted alone, an automation edit and a hand edit are the same
        number, and `land_pr.py` rewrites the referenced issue's body on every
        land), and must carry its own ceiling -- GraphQL's counter has the same
        absence-read-as-negative shape one level down.
        """
        self.assertTrue(driver.BLIND_PROBES)
        for probe, blind in driver.BLIND_PROBES.items():
            with self.subTest(probe=probe):
                self.assertTrue(blind["pattern"].search("issues/72/events"))
                self.assertIn("userContentEdits", blind["instead"])
                self.assertIn("editor{login}", blind["instead"])
                self.assertIn("ABSENT", blind["ceiling"])
                self.assertIn("ed3c/skill-concerns#102", blind["ceiling"])
                # Not a paraphrase of the ceiling: the sentence
                # `scripts/check_second_arrival_ceiling.py` owns for every
                # carrier in the tree, quoted here so drifting either side
                # reds (ed3c/skill-concerns#102, #135).
                self.assertIn(
                    "userContentEdits.totalCount counts the ORIGINAL revision: 0 is ABSENT, the first edit moves it 0 -> 2, and every later edit by one (ed3c/skill-concerns#102)",  # noqa: E501
                    blind["ceiling"],
                )

    def test_the_probe_matches_the_placeholder_a_lane_actually_writes(self) -> None:
        """A detector anchored on `\\d+` reads the fixture and nothing else.

        Lane reports cite the probe with the issue number left as a
        placeholder. Measured across wave-21's four lane reports, the forms
        written were `issues/N/events` and `issues/<n>/events`; the literal
        `issues/72/events` appears only in the fixture this class was filed
        from. So the pattern that "detects" this class was structurally silent
        on every document it was pointed at -- an observer blind to the thing
        it is cited for, which is the class itself, one level up.
        """
        blind = driver.BLIND_PROBES["rest-events-edited"]
        for citation in (
            "gh api repos/ed3c/skill-concerns/issues/N/events",
            "repos/OWNER/REPO/issues/<n>/events",
            "issues/{number}/timeline",
            "issues/72/events",
        ):
            with self.subTest(citation=citation):
                self.assertTrue(blind["pattern"].search(citation), citation)

    def test_a_document_naming_the_sighted_surface_is_disposed_not_hit(self) -> None:
        """The acquittal the widening has to come with.

        Widening the pattern without this fires on every correct disposition --
        this module's own comment, the catalogue recipe, and every lane report
        that adopted the GraphQL surface all cite the blind probe in order to
        refuse it. The class is "an absence claim RESTS on a blind observer",
        so a document that already names the surface which can carry the answer
        has grounded its claim, not abandoned it.

        Both arms in one bundle, so the conjunction is shown to be load-bearing
        rather than asserted.
        """
        bundle = self.scratch / "sighted-bundle"
        (bundle / "reports").mkdir(parents=True)
        resting = (
            "Second arrival: `gh api repos/ed3c/skill-concerns/issues/N/events`\n"
            "-- no body edit by this lane and none by automation.\n"
        )
        disposed = resting + (
            "REST is blind here; read it via authenticated gh api graphql "
            "instead, totalCount=0 -> ABSENT.\n"
        )
        # The third arm is the one the mandatory ceiling created. It carries
        # the sentence `scripts/check_second_arrival_ceiling.py` orders every
        # carrier in this tree to paste, verbatim and complete, and nothing
        # else -- so an acquittal keyed on the bare token `userContentEdits`
        # would be free for exactly the documents most likely to have pasted
        # it without reading anything. The vacuity guards below are what make
        # this arm mean that: it really does contain the token, and really
        # does not name the surface.
        boilerplate = resting + (
            "userContentEdits.totalCount counts the ORIGINAL revision: 0 is ABSENT, "
            "the first edit moves it 0 -> 2, and every later edit by one "
            "(ed3c/skill-concerns#102).\n"
        )
        # Wave 21's L2 disposal line, quoted from ed3c/skill-concerns#129's
        # body: it names the CONNECTION and not the surface, and it is a
        # correct disposition. The acquittal has to keep taking it, or the
        # boilerplate cure would red the real reports this atom exists for.
        connection = resting + (
            "REST is structurally blind here and was not consulted; second "
            "arrival is `userContentEdits` totalCount=0 -> ABSENT.\n"
        )
        for name, text in (
            ("lane-report-resting.md", resting),
            ("lane-report-disposed.md", disposed),
            ("lane-report-boilerplate.md", boilerplate),
            ("lane-report-connection.md", connection),
        ):
            (bundle / "reports" / name).write_text(text, encoding="utf-8")
        self.assertNotIn("graphql", boilerplate.lower(), "the arm is vacuous")
        self.assertIn("userContentEdits", boilerplate)
        self.assertNotIn("graphql", connection.lower(), "the arm is vacuous")
        self.assertIn("userContentEdits", connection)
        hits = driver.EXPERIMENTS["blind-observer"](bundle)
        self.assertEqual(
            ["reports/lane-report-boilerplate.md", "reports/lane-report-resting.md"],
            sorted(hit["subject"]["path"] for hit in hits),
        )

    def test_the_claim_half_reads_the_words_wave_21_lanes_actually_wrote(self) -> None:
        """ed3c/skill-concerns#129: `body edit` is in no lane report.

        The three citations below are QUOTED from #129's body, which measured
        them across wave 21's four lane reports: `issues/<n>/events` and
        `issues/N/events` as the probe spelling, `totalCount=0 -> ABSENT` as
        the absence, and L2's disposal line verbatim. The reports themselves
        never entered this tree, so this runs their vocabulary through the
        fixed detector and is not the replay #129's last clause asks for --
        that clause is answered in the issue, not here.

        The vacuity guard is the load-bearing line: each positive arm is
        asserted to contain no `body edit`, so it can only be matched by the
        widening this atom lands.
        """
        bundle = self.scratch / "wave-21-vocabulary"
        (bundle / "reports").mkdir(parents=True)
        resting = {
            "lane-report-l2-resting.md": (
                "Second arrival: `gh api repos/ed3c/skill-concerns/issues/<n>/events`\n"
                "-- totalCount=0 -> ABSENT.\n"
            ),
            "lane-report-l3-resting.md": (
                "SECOND ARRIVAL: issues/N/events returned nothing, so ABSENT.\n"
            ),
        }
        disposed = {
            "lane-report-l2-disposed.md": (
                "REST `issues/<n>/events` is structurally blind here and was not "
                "consulted; second arrival is `userContentEdits` totalCount=0 "
                "-> ABSENT.\n"
            ),
        }
        for name, text in {**resting, **disposed}.items():
            (bundle / "reports" / name).write_text(text, encoding="utf-8")

        for name, text in resting.items():
            with self.subTest(positive=name):
                self.assertNotIn("body edit", text.lower(), "the arm is vacuous")
                self.assertTrue(driver.ABSENCE_CLAIM.search(text))

        hits = driver.EXPERIMENTS["blind-observer"](bundle)
        self.assertEqual(
            sorted(f"reports/{name}" for name in resting),
            sorted(hit["subject"]["path"] for hit in hits),
        )

    def test_a_diagnostic_name_ending_in_the_state_is_not_an_absence_claim(self) -> None:
        """The planted negative for the widening's own false positive.

        `RECEIPT_PRODUCER_ABSENT` is a diagnostic, not a claim, and the
        wave-17 fixture carries it beside the probe citation. A claim half
        matching the bare state without a word boundary would have turned
        every finding that names that diagnostic into a blind-observer hit --
        and the committed wave-17 record, which is append-only, says the count
        there is one.
        """
        self.assertIsNone(driver.ABSENCE_CLAIM.search("RECEIPT_PRODUCER_ABSENT"))
        self.assertEqual(
            1, len(driver.EXPERIMENTS["blind-observer"](WAVE_17)),
            "the committed wave-17 record's blind-observer count is 1 and the "
            "ledger is append-only",
        )

    def test_the_blind_observer_finding_points_at_the_sighted_surface(self) -> None:
        """Direct readback: a lane reads the finding, not this table.

        The disposition has to reach the artifact a reader actually receives,
        or it is a comment in a file nobody opens -- which is the defect class
        this atom is an instance of.
        """
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        blind = [
            finding
            for finding in report["findings"]
            if finding["catalogue_class"] == "blind-observer"
        ]
        self.assertTrue(blind)
        observed = blind[0]["experiment"]["observed"]
        self.assertIn("rest-events-edited", observed)
        self.assertIn("userContentEdits", observed)
        self.assertIn("editor{login}", observed)
        self.assertIn("ed3c/skill-concerns#102", observed)
        # And it survives the trip into an issue body, fences and all.
        block = driver.render_demonstration(blind[0])
        body = TEMPLATE.read_text(encoding="utf-8").replace("{demonstration}", block)
        self.assertEqual([], validator.completeness_reasons(body, HONEST_NONE))
        self.assertIn("userContentEdits", body)

    def test_the_catalogue_recipe_reads_the_sighted_surface_with_its_editors(self) -> None:
        """The recipe an operator RUNS, not only the table the driver reads."""
        entry = next(
            item for item in catalogue()["classes"] if item["id"] == "blind-observer"
        )
        recipe = entry["falsification"]["recipe"]
        sighted = [step for step in recipe if "userContentEdits" in step]
        self.assertEqual(1, len(sighted), recipe)
        self.assertIn("nodes{editedAt editor{login}}", sighted[0])
        # The blind step stays: it is the contrast the class is made of, and
        # the fixture it reproduces is a committed lane report, not an
        # instrument anyone is being told to use.
        self.assertTrue([step for step in recipe if "/events" in step])

    def test_gen_red_team_receipts_is_idempotent_and_authors_the_committed_bytes(self) -> None:
        rendered = gen_red_team_receipts.render(catalogue())
        self.assertEqual(
            (SKILL_ROOT / "receipts.json").read_text(encoding="utf-8"), rendered
        )
        self.assertEqual(gen_red_team_receipts.render(catalogue()), rendered)

    def test_an_adjudicated_class_folds_in(self) -> None:
        """The planted negative control for the BUILD refusal below."""
        entry = {
            "id": "planted-adjudicated-class",
            "cure_authorization": dict(cure_authorization.ADJUDICATED_AUTHORIZATION),
        }
        grown = driver.add_class(catalogue(), entry)
        self.assertEqual(len(grown["classes"]), len(catalogue()["classes"]) + 1)

    # ------------------------------------- the verdict field (skill-concerns#152)

    def _dispositions(self, name: str, *rows: dict) -> Path:
        path = self.scratch / f"adjudications-{name}.json"
        path.write_text(
            json.dumps({"schema_version": 1, "adjudications": list(rows)}, indent=2),
            encoding="utf-8",
        )
        return path

    def _disposition(self, finding: dict, verdict: str, ground: str) -> dict:
        return {
            "catalogue_class": finding["catalogue_class"],
            "subject": dict(finding["subject"]),
            "verdict": verdict,
            "ground": ground,
        }

    def _wave_17(self, filed: dict | None = None) -> dict:
        return driver.run(
            WAVE_17, catalogue(), "wave-17", "admission-fixture", filed=filed
        )

    def test_an_unadjudicated_hit_reaches_confirmed_and_says_it_was_unadjudicated(self) -> None:
        """The default, unchanged: #152 makes no claim any committed CONFIRMED was wrong.

        What is new is that CONFIRMED is a branch over an input rather than the
        only string the code can write, and the record says which branch it took.
        """
        report = self._wave_17()
        self.assertTrue(report["findings"])
        self.assertEqual(
            {"CONFIRMED": len(report["findings"]), "REFUTED": 0, "INCONCLUSIVE": 0},
            report["verdicts"],
        )
        for finding in report["findings"]:
            self.assertEqual(driver.DEFAULT_GROUND, finding["adjudication"])

    def test_a_refuted_disposition_reaches_refuted_in_a_run(self) -> None:
        """The state the wave-24 discards needed and could not receive.

        Demonstrated by a RUN whose record carries it, never by constructing the
        record - a test that builds a `REFUTED` dict passes against a mono-state
        instrument, which is the whole reason #152 exists.
        """
        target = self._wave_17()["findings"][0]
        filed = driver.load_adjudications(
            self._dispositions(
                "refuted",
                self._disposition(
                    target,
                    "REFUTED",
                    "the class's recipe ran against these exact bytes and came back the "
                    "other way; the match is a coincidence of shape",
                ),
            )
        )
        report = self._wave_17(filed)
        reached = {finding["id"]: finding for finding in report["findings"]}
        self.assertEqual("REFUTED", reached[target["id"]]["verdict"])
        self.assertEqual(1, report["verdicts"]["REFUTED"])
        self.assertEqual([], validator.finding_errors(reached[target["id"]]))
        self.assertIn("came back the other way", reached[target["id"]]["adjudication"])

    def test_an_inconclusive_disposition_reaches_inconclusive_in_a_run(self) -> None:
        """The third state, produced the same way and counted separately."""
        target = self._wave_17()["findings"][0]
        filed = driver.load_adjudications(
            self._dispositions(
                "inconclusive",
                self._disposition(
                    target,
                    "INCONCLUSIVE",
                    "the subject the recipe needs was triaged ABSENT at this boundary, so "
                    "neither direction was reached",
                ),
            )
        )
        report = self._wave_17(filed)
        reached = {finding["id"]: finding for finding in report["findings"]}
        self.assertEqual("INCONCLUSIVE", reached[target["id"]]["verdict"])
        self.assertEqual(1, report["verdicts"]["INCONCLUSIVE"])
        self.assertEqual(0, report["verdicts"]["REFUTED"])

    def test_the_demonstration_block_carries_the_verdict_and_its_ground(self) -> None:
        """A verdict a reader cannot trace to a ground is prose with a state name."""
        target = self._wave_17()["findings"][0]
        filed = driver.load_adjudications(
            self._dispositions(
                "rendered",
                self._disposition(target, "REFUTED", "the recipe came back negative here"),
            )
        )
        finding = {
            item["id"]: item for item in self._wave_17(filed)["findings"]
        }[target["id"]]
        block = driver.render_demonstration(finding)
        self.assertIn("- verdict: REFUTED", block)
        self.assertIn("- adjudication: the recipe came back negative here", block)

    # ---------------------------------------------------------------- negative

    def test_a_disposition_bound_to_other_bytes_blocks_the_pass(self) -> None:
        """A triage carried forward onto changed bytes is not a verdict."""
        target = self._wave_17()["findings"][0]
        row = self._disposition(target, "REFUTED", "ran and came back negative")
        row["subject"] = {**row["subject"], "sha256": "0" * 64}
        report = self._wave_17(driver.load_adjudications(self._dispositions("stale", row)))
        self.assertEqual("blocked", report["outcome"])
        self.assertEqual([], report["findings"])
        self.assertTrue(
            report["refusal"].startswith(driver.ADJUDICATION_STALE), report["refusal"]
        )

    def test_a_verdict_with_no_ground_blocks_the_pass(self) -> None:
        """A bare state name is the number that was typed, one level up."""
        target = self._wave_17()["findings"][0]
        report = self._wave_17(
            driver.load_adjudications(
                self._dispositions("ungrounded", self._disposition(target, "REFUTED", "   "))
            )
        )
        self.assertEqual("blocked", report["outcome"])
        self.assertIn("states no ground", report["refusal"])

    def test_a_verdict_outside_the_declared_states_blocks_the_pass(self) -> None:
        """The tuple is the vocabulary for the input too, not only for the output."""
        target = self._wave_17()["findings"][0]
        report = self._wave_17(
            driver.load_adjudications(
                self._dispositions(
                    "outside", self._disposition(target, "PROBABLY", "it looked wrong")
                )
            )
        )
        self.assertEqual("blocked", report["outcome"])
        self.assertTrue(
            report["refusal"].startswith(driver.ADJUDICATION_UNGROUNDED), report["refusal"]
        )

    def test_two_dispositions_of_one_hit_are_refused_rather_than_resolved(self) -> None:
        """Picking one silently is how a disagreement becomes a verdict nobody made."""
        target = self._wave_17()["findings"][0]
        path = self._dispositions(
            "double",
            self._disposition(target, "REFUTED", "the recipe came back negative"),
            self._disposition(target, "CONFIRMED", "on second thought the match stands"),
        )
        with self.assertRaises(driver.AdjudicationRefused) as raised:
            driver.load_adjudications(path)
        self.assertIn("adjudicated twice", str(raised.exception))

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

    def test_the_dropped_assertion_would_have_survived_its_own_falsification(self) -> None:
        """ed3c/skill-concerns#137: why the old fenced-block control was DELETED.

        It read `any("Observer demonstration" in reason for reason in
        completeness_reasons(fenced))` and called that "a fenced demonstration is
        refused". After ed3c/noodles#317 the fence-preserving reader admits that
        body -- but the missing-MARKER reason names the same heading verbatim, so
        the substring still matches and the assertion still passes. A control
        that survives the removal of the property it tests is not a control, and
        rewriting it in place would have left the false green standing.

        Its subject is now split across two tests that name their reader:
        `..._graded_by_the_reader_that_keeps_fences` and
        `..._fenced_required_section_still_reds_the_reader_that_strips`.
        """
        report = driver.run(WAVE_17, catalogue(), "wave-17", "admission-fixture")
        block = driver.render_demonstration(report["findings"][0])
        fenced = TEMPLATE.read_text(encoding="utf-8").replace(
            "{demonstration}", f"```\n{block}\n```"
        )
        undeclared = validator.completeness_reasons(fenced)
        self.assertTrue(
            any("Observer demonstration" in reason for reason in undeclared),
            "the old assertion's exact expression -- still true, for a reason it "
            "was never about",
        )
        self.assertTrue(
            all("carries no authored assertion" not in reason for reason in undeclared),
            "and the refusal it MEANT is gone: nothing grades that section with "
            "fences stripped any more",
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
                "not what gen_red_team_receipts.py produces" in error
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
                {"subject": STATION, "wave": f"wave-{index}", "hits": {"blind-observer": 2}}
                for index in (17, 18, 19)
            ]
        }
        self.assertIn("CURVE_NOT_DECLINING", "\n".join(driver.curve_findings(flat)))
        bending = {
            "records": [
                {"subject": STATION, "wave": "wave-17", "hits": {"blind-observer": 3}},
                {"subject": STATION, "wave": "wave-18", "hits": {"blind-observer": 2}},
                {"subject": STATION, "wave": "wave-19", "hits": {"blind-observer": 1}},
            ]
        }
        self.assertEqual([], driver.curve_findings(bending))
        self.assertEqual([], driver.curve_findings({"records": flat["records"][:2]}))

    def test_a_station_resting_at_zero_is_the_success_state_not_a_finding(self) -> None:
        """The floor guard, and the pair that makes it discriminating.

        `[0, 0, 0]` is a station whose classes ARE gating - this bundle's
        declared steady state - and a strict `recent[-1] < recent[0]` reads it
        as never having bent, so R7 would fire on success forever once the
        classes did their job. The negative arm is the same station one point
        later at `[0, 0, 1]`: recurrence coming back off the floor still
        reports, so the guard is a floor and not a mute.
        """
        floor = {
            "records": [
                {"subject": STATION, "wave": f"wave-{index}", "hits": {"blind-observer": 0}}
                for index in (17, 18, 19)
            ]
        }
        self.assertEqual(
            [("wave-17", 0), ("wave-18", 0), ("wave-19", 0)],
            driver.curve(floor, STATION),
        )
        self.assertEqual([], driver.curve_findings(floor))

        off_the_floor = {
            "records": [
                *floor["records"][:2],
                {"subject": STATION, "wave": "wave-19", "hits": {"blind-observer": 1}},
            ]
        }
        self.assertIn("[0, 0, 1]", "\n".join(driver.curve_findings(off_the_floor)))

    def test_every_non_declining_station_reaches_the_dispatcher(self) -> None:
        """Two stations stopped bending; a first-match readback reported one.

        The station that never printed is indistinguishable from a station
        that declined - the hides-inside-a-bigger-one shape one level up from
        the blend this atom replaced. Both are asserted by name, and the third,
        which IS declining, is asserted absent so the arm is not merely
        counting lines.
        """
        ledger = {
            "records": [
                {"subject": station, "wave": f"wave-{wave}", "hits": {"blind-observer": count}}
                for station, counts in (
                    ("station-a", (1, 1, 1)),
                    ("station-b", (2, 3, 4)),
                    ("station-c", (9, 5, 1)),
                )
                for wave, count in zip((17, 18, 19), counts)
            ]
        }
        findings = driver.curve_findings(ledger)
        self.assertEqual(2, len(findings), findings)
        self.assertEqual(
            ["station-a", "station-b"],
            [finding.split(":")[1] for finding in findings],
        )
        self.assertNotIn("station-c", "\n".join(findings))

    def test_the_curve_is_sliced_by_station_and_the_blend_hides_one(self) -> None:
        """ed3c/skill-concerns#130's planted control: two stations, one hidden.

        `wave-boundary` is gating - 10, 5, 1. `noodles-generation-close` is
        not - 1, 2, 3. Summed by wave the series is 11, 7, 4, which DECLINES,
        so the blended readback the ledger shipped with returns nothing at all
        while a station that stopped gating sits inside it. The blend is
        computed here in the reading this atom replaces, so the arm measures
        the difference rather than asserting it.
        """
        ledger = {
            "records": [
                {"subject": station, "wave": f"wave-{wave}", "hits": {"blind-observer": count}}
                for station, counts in (
                    ("wave-boundary", (10, 5, 1)),
                    (STATION, (1, 2, 3)),
                )
                for wave, count in zip((17, 18, 19), counts)
            ]
        }
        self.assertEqual(["wave-boundary", STATION], driver.stations(ledger))
        self.assertEqual(
            [("wave-17", 10), ("wave-18", 5), ("wave-19", 1)],
            driver.curve(ledger, "wave-boundary"),
        )
        self.assertEqual(
            [("wave-17", 1), ("wave-18", 2), ("wave-19", 3)],
            driver.curve(ledger, STATION),
        )

        blended: dict[str, int] = {}
        for record in ledger["records"]:
            blended[record["wave"]] = blended.get(record["wave"], 0) + sum(
                record["hits"].values()
            )
        self.assertEqual([11, 7, 4], list(blended.values()))
        self.assertLess(
            list(blended.values())[-1],
            list(blended.values())[0],
            "the arm is vacuous unless the blended series looks green",
        )

        finding = "\n".join(driver.curve_findings(ledger))
        self.assertIn("CURVE_NOT_DECLINING", finding)
        self.assertIn(STATION, finding)
        self.assertIn("[1, 2, 3]", finding)
        self.assertNotIn("wave-boundary", finding)

    def test_a_ledger_column_that_disagrees_with_its_own_hits_reds(self) -> None:
        """`judge_gaps` and `duplicate_blocks` are views, never measurements.

        Both derive from the record's own `hits`, so a hand-triaged number
        typed into a committed record is the one thing a single file state can
        refuse (ed3c/skill-concerns#130). Positive arm first: every committed
        record's columns already reconcile, so the negative arm is not passing
        on a ledger that never agreed.
        """
        for position, record in enumerate(domain("run-ledger.json")["records"]):
            with self.subTest(record=position):
                self.assertEqual([], validator.derived_column_errors(position, record))

        copy = self.copy()
        path = copy / "domain" / "run-ledger.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["records"][-1]["judge_gaps"] = 4
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "judge_gaps=4 disagrees with its own hits" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_a_flat_curve_leaves_through_the_exit_code(self) -> None:
        """R7 is a finding, so it does not exit 0 as stdout prose.

        A finding that leaves the process at status 0 is consumed by nobody:
        the caller that would act on it reads the exit code. The run itself is
        clean here, so a non-zero status can only have come from the curve.

        The standing curve is `[1, 1, 1]` at `wave-boundary` and the clean run
        is appended at ANOTHER station, which is the honest shape twice over.
        A clean run at the reported station puts a zero on the end of its own
        series, and a series ending at the floor is the success state rather
        than a flat one (the guard in `curve_findings`) - so the old form of
        this arm, three empty records at one station, measured the defect it
        would now be asserting. And a station that stopped bending must not be
        silenced by a clean pass somewhere else, which is what per-station
        slicing buys.
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
                            "subject": driver.DEFAULT_SUBJECT,
                            "classes_sampled": [],
                            "hits": {"blind-observer": 1},
                            "novel_class_candidates": [],
                            "judge_gaps": 1,
                            "duplicate_blocks": 0,
                        }
                        for day in (10, 11, 12)
                    ]
                }
            ),
            encoding="utf-8",
        )
        status = driver.main(
            [
                "--bundle", str(CLEAN),
                "--wave", "wave-13",
                "--subject", STATION,
                "--ledger", str(ledger),
                "--append-record",
            ]
        )
        self.assertEqual(
            "clean",
            driver.run(CLEAN, catalogue(), "wave-13", "stage-close")["outcome"],
        )
        self.assertNotEqual(0, status)
        appended = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertEqual(STATION, appended["records"][-1]["subject"])
        self.assertEqual(
            [driver.DEFAULT_SUBJECT],
            [finding.split(":")[1] for finding in driver.curve_findings(appended)],
        )

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
        path = copy / "scripts" / "gen_red_team_receipts.py"
        path.write_text(
            "import subprocess\n" + path.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.assertTrue(
            any(
                "DRIVER_SURFACE_FORBIDDEN:gen_red_team_receipts.py" in error
                and "spawn a process" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_a_named_neighbour_absent_from_the_tree_fails(self) -> None:
        """A boundary term is verified against bytes, or it is a claim.

        This assertion is the successor of the absent-neighbour exit, which
        expired when `shadow-architect` landed (ed3c/skill-concerns#75): the
        exit fired by landed state, not by anyone remembering it, and it was
        removed rather than left standing. What remains falsifiable is the
        arm that outlives it -- every named neighbour must resolve to bytes in
        the tree being validated, and one that does not is reported as absent
        rather than read as agreement.
        """
        fake_repo = self.scratch / "repo"
        for name in list(validator.NEIGHBOURS)[:-1]:
            (fake_repo / "skills" / name).mkdir(parents=True)
        missing = list(validator.NEIGHBOURS)[-1]
        self.assertTrue(
            any(
                f"neighbour {missing} named but absent from this tree" in error
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

    # -------------------------------------------- the generation-close station

    def test_the_station_record_is_what_the_fixture_generation_produces(self) -> None:
        """The committed generation-close record is derived, and zero writes happened.

        The fixture bundle carries the three kinds the station's topology row
        enumerates and one known catalogue-class instance. The record is what
        the run produces, the finding satisfies the schema, and the bundle's
        digest is the same before and after - measured, not promised.
        """
        committed = dict(
            next(
                record
                for record in domain("run-ledger.json")["records"]
                if record["subject"] == STATION
            )
        )
        self.assertEqual(
            driver.sampled_classes(catalogue())[: len(committed["classes_sampled"])],
            committed["classes_sampled"],
            "BUILD only ever appends, so the classes in force at a record's "
            "instant are a PREFIX of today's active list; a record that names a "
            "class the catalogue never carried, or that skips one it did, has "
            "been edited rather than measured",
        )
        report = driver.run(
            GENERATION_CLOSE,
            catalogue_as_of(committed),
            "generation-fixture",
            "generation-close-fixture",
            subject_kind=STATION,
        )
        self.assertTrue(report["read_only"]["held"])
        self.assertEqual(
            ["free-exit"], [finding["catalogue_class"] for finding in report["findings"]]
        )
        for finding in report["findings"]:
            self.assertEqual([], validator.finding_errors(finding))
        produced = driver.ledger_record(report)
        produced.pop("run_id")
        committed.pop("run_id")
        self.assertEqual(committed, produced)

    def test_a_clean_bundle_at_the_station_still_appends_its_record(self) -> None:
        """The planted negative arm: no findings, and the record lands anyway.

        A station whose clean runs leave no trace is a station whose silence
        cannot be told from its absence, which is the whole reason the record
        is the close-out step's receipt.
        """
        ledger = self.scratch / "station-ledger.json"
        ledger.write_text(json.dumps({"records": []}), encoding="utf-8")
        status = driver.main(
            [
                "--bundle", str(CLEAN),
                "--wave", "generation-clean-fixture",
                "--boundary", "generation-close-fixture",
                "--subject", STATION,
                "--ledger", str(ledger),
                "--append-record",
            ]
        )
        self.assertEqual(0, status)
        records = json.loads(ledger.read_text(encoding="utf-8"))["records"]
        self.assertEqual(1, len(records))
        self.assertEqual(STATION, records[0]["subject"])
        self.assertEqual(0, records[0]["judge_gaps"])
        self.assertEqual({0}, set(records[0]["hits"].values()))

    def test_a_graduated_class_is_absent_from_the_next_runs_sampled_list(self) -> None:
        """Graduation, read back off the run record rather than off the filter.

        A class whose recipe has become a machine elsewhere is marked gated with
        its gate reference, and the very next run must not sample it. Both
        directions: the same fixture with the class still active does.
        """
        active = driver.ledger_record(
            driver.run(GENERATION_CLOSE, catalogue(), "g", "generation-close-fixture", subject_kind=STATION)
        )
        self.assertIn("free-exit", active["classes_sampled"])
        self.assertEqual(1, active["hits"]["free-exit"])

        graduated = catalogue()
        for entry in graduated["classes"]:
            if entry["id"] == "free-exit":
                entry["status"] = "gated"
                entry["gate_ref"] = "a consumer CI gate landed by an ordinary atom"
        record = driver.ledger_record(
            driver.run(GENERATION_CLOSE, graduated, "g", "generation-close-fixture", subject_kind=STATION)
        )
        self.assertNotIn("free-exit", record["classes_sampled"])
        self.assertNotIn("free-exit", record["hits"])
        self.assertEqual(0, record["judge_gaps"])

    def test_a_run_record_naming_an_undeclared_station_reds(self) -> None:
        """The subject vocabulary is the topology's ids, not a second list."""
        copy = self.copy()
        path = copy / "domain" / "run-ledger.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["records"][0]["subject"] = "a-seam-nobody-declared"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "OBSERVATION_TARGET_UNGROUNDED:run record 0" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_the_stations_runbook_step_names_its_completion_receipt(self) -> None:
        """Positive control for the runbook pointer, and its negative arm."""
        target = next(
            row
            for row in domain("observation-topology.json")["targets"]
            if row["id"] == STATION
        )
        runbook = SKILL_ROOT / target["runbook"]["path"]
        self.assertIn(target["runbook"]["step"], runbook.read_text(encoding="utf-8"))
        self.assertTrue((SKILL_ROOT / target["runbook"]["receipt"]).is_file())

        copy = self.copy()
        (copy / target["runbook"]["path"]).unlink()
        self.assertTrue(
            any(
                "does not resolve, so the named close-out step" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

    def test_an_arrival_row_claiming_a_run_the_ledger_never_recorded_reds(self) -> None:
        """The other direction of the arrival tie.

        The station reaches PRODUCTION only when a real generation's record and
        the row's run receipt arrive together; a row that claims the receipt
        while every record came from a fixture is the overclaim the arrival
        ledger exists to catch, seen from this side.
        """
        fake_repo = self.scratch / "repo"
        for name in validator.NEIGHBOURS:
            (fake_repo / "skills" / name).mkdir(parents=True)
        topology = fake_repo / validator.ARRIVAL_TOPOLOGY
        topology.parent.mkdir(parents=True, exist_ok=True)
        topology.write_text(
            json.dumps(
                {
                    "rows": [
                        {
                            "id": "sc-red-team-generation-close-station",
                            "receipts": [{"kind": "run", "ref": "a generation that never ran"}],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.assertTrue(
            any(
                "STATION_ARRIVAL_UNTIED" in error and "came from a fixture" in error
                for error in validator.validate(SKILL_ROOT, fake_repo)
            )
        )

    # ------------------------------------------ the residual-sensor register

    def test_every_register_sensor_is_a_readback_that_exists(self) -> None:
        """Each row's sensor names bytes this tree can open, holding its phrase.

        A register whose sensors point at duties nobody wrote reads as coverage
        while watching nothing, which is the gap class it exists to record.
        """
        rows = domain("residual-sensor-register.json")["rows"]
        self.assertEqual(5, len(rows))
        for row in rows:
            with self.subTest(row=row["id"]):
                readback = REPO_ROOT / row["sensor"]["readback"]
                self.assertTrue(readback.is_file())
                self.assertIn(row["sensor"]["phrase"], readback.read_text(encoding="utf-8"))
                self.assertTrue(str(row["escalation"]["trigger"]).strip())
                self.assertTrue(str(row["escalation"]["path"]).strip())
        gated = next(row for row in rows if row["id"] == "match-without-experiment")
        self.assertEqual("GATED", gated["status"])
        self.assertTrue(str(gated["gate_ref"]).strip())

    def test_a_register_row_missing_any_required_field_reds(self) -> None:
        """All four fields, each proven load-bearing on its own."""
        for field in validator.REGISTER_FIELDS:
            with self.subTest(field=field):
                copy = self.copy()
                path = copy / "domain" / "residual-sensor-register.json"
                body = json.loads(path.read_text(encoding="utf-8"))
                body["rows"][0].pop(field)
                path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
                self.assertTrue(
                    any(
                        "CEILING_WITHOUT_SENSOR" in error and field in error
                        for error in validator.validate(copy, REPO_ROOT)
                    )
                )

    def test_a_prose_ceiling_with_no_register_row_reds(self) -> None:
        """The reflexive rule, on a document and on a script alike."""
        for relative in ("SKILL.md", "scripts/shadow_driver.py"):
            with self.subTest(relative=relative):
                copy = self.copy()
                path = copy / relative
                path.write_text(
                    path.read_text(encoding="utf-8")
                    + "\n# sampling stays a judgement here, a structural ceiling\n",
                    encoding="utf-8",
                )
                self.assertTrue(
                    any(
                        "no register row is named" in error
                        for error in validator.validate(copy, REPO_ROOT)
                    )
                )

    def test_a_register_status_and_its_landed_ref_move_together(self) -> None:
        """Both directions of the status the rubber-stamp row now carries.

        The row says the sensor fired and the escalation landed; stripping the
        ref that says WHERE it landed leaves a status nobody can read back, and
        a landed ref on a row still marked OPEN is the same drift the other way.
        """
        rows = domain("residual-sensor-register.json")["rows"]
        fired = next(row for row in rows if row["id"] == "rubber-stamp-authorization")
        self.assertEqual("SENSOR_FIRED_ESCALATION_LANDED", fired["status"])
        self.assertEqual("ed3c/skill-concerns#103", fired["escalation"]["landed"])

        stripped = self.copy()
        path = stripped / "domain" / "residual-sensor-register.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["rows"][0]["escalation"].pop("landed")
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "is not a provider ref that says where" in error
                for error in validator.validate(stripped, REPO_ROOT)
            )
        )

        stale = self.copy()
        path = stale / "domain" / "residual-sensor-register.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        open_row = next(row for row in body["rows"] if row["status"] == "OPEN")
        open_row["escalation"]["landed"] = "ed3c/skill-concerns#103"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "while the row is still OPEN" in error
                for error in validator.validate(stale, REPO_ROOT)
            )
        )

    def test_the_two_method_claims_resolve_to_a_real_adjudication_artifact(self) -> None:
        """The in-atom disposition of both live rows, read back.

        Each names a pinned subject that exists and that its own ref repeats,
        and an adjudication issue that is also one of the claim's refs - so the
        cadence sweep that already re-resolves receipts refs is what keeps the
        artifact existing. The judge's garbage ref is refused on the same call.
        """
        claims = catalogue()["method_claims"]
        self.assertEqual(2, len(claims))
        for claim_id, claim in sorted(claims.items()):
            with self.subTest(claim=claim_id):
                authorization = claim["authorization"]
                subject = authorization["subject"]
                self.assertIn(subject, authorization["ref"])
                self.assertTrue((REPO_ROOT / subject).exists())
                issue = authorization["adjudication"]["issue"]
                self.assertIn(issue, claim["refs"])
                self.assertEqual(
                    [],
                    cure_authorization.authorization_errors(
                        authorization, tree=REPO_ROOT
                    ),
                )

        errors: list[str] = []
        vibes = {
            "method_claims": {
                "planted": {
                    "claim": "the vibes were good",
                    "refs": ["ed3c/skill-concerns#94"],
                    "authorization": {
                        "kind": "operator-adjudication",
                        "ref": cure_authorization.VIBES_REF,
                    },
                }
            }
        }
        validator.check_method_claims(vibes, REPO_ROOT, errors)
        self.assertTrue(any("names no adjudication artifact" in error for error in errors))

    def test_an_adjudication_issue_outside_the_claims_refs_reds(self) -> None:
        """Existence-checked means a reader re-resolves it, not that it parses.

        `gen_red_team_receipts` projects a claim's refs into receipts.json and the
        maintain cadence re-resolves every ref it finds there. An adjudication
        issue that is not among those refs is an artifact nothing re-reads.
        """
        copy = self.copy()
        path = copy / "domain" / "catalogue.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        for claim in body["method_claims"].values():
            claim["authorization"]["adjudication"]["issue"] = "ed3c/skill-concerns#1"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(
            any(
                "is not among the claim's refs" in error
                for error in validator.validate(copy, REPO_ROOT)
            )
        )

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
