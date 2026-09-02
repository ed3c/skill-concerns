from __future__ import annotations

import ast
import copy
import json
from datetime import date
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_admissions  # noqa: E402
import check_agents_hops  # noqa: E402
import check_skill_bundles  # noqa: E402
import cure_authorization  # noqa: E402
from common import digest_entries, regular_files, tree_digest  # noqa: E402
from freeze_source import build_lock  # noqa: E402


class RepositoryControlTests(unittest.TestCase):
    def write_route_repo(self, root: Path, routes: dict[str, list[str]], maximum: int) -> None:
        for node, children in routes.items():
            path = root / node
            path.parent.mkdir(parents=True, exist_ok=True)
            marker = "none" if not children else ",".join(children)
            path.write_text(f"<!-- agent-next: {marker} -->\n", encoding="utf-8")
        (root / "agents-routing.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "root": "AGENTS.md",
                    "max_documents": maximum,
                    "routes": routes,
                }
            ),
            encoding="utf-8",
        )

    def test_current_three_document_route_passes(self) -> None:
        self.assertEqual([], check_agents_hops.check(ROOT))

    def test_fourth_agent_document_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            routes = {
                "AGENTS.md": ["skills/AGENTS.md"],
                "skills/AGENTS.md": ["skills/demo/AGENTS.md"],
                "skills/demo/AGENTS.md": ["skills/demo/nested/AGENTS.md"],
                "skills/demo/nested/AGENTS.md": [],
            }
            self.write_route_repo(temp, routes, 3)
            errors = check_agents_hops.check(temp)
            self.assertTrue(
                any(error.startswith("AGENT_ROUTE_DEPTH:4") for error in errors),
                errors,
            )
            self.assertTrue(
                any(error.startswith("SKILL_AGENT_DOCUMENT_NESTED") for error in errors),
                errors,
            )

    def test_agent_route_cycle_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            routes = {
                "AGENTS.md": ["skills/AGENTS.md"],
                "skills/AGENTS.md": ["AGENTS.md"],
            }
            self.write_route_repo(temp, routes, 3)
            errors = check_agents_hops.check(temp)
            self.assertTrue(
                any(error.startswith("AGENT_ROUTE_CYCLE") for error in errors),
                errors,
            )

    def test_forbidden_domain_literal_fails_portable_core(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory)
            (skill / "SKILL.md").write_text(
                "use control-glass directly\n", encoding="utf-8"
            )
            errors = check_skill_bundles.scan_forbidden_literals(
                skill, ["SKILL.md"], ["control-glass"]
            )
            self.assertEqual(
                ["DOMAIN_LITERAL_IN_PORTABLE_CORE:SKILL.md:control-glass"],
                errors,
            )

    def test_hollow_executable_route_fails(self) -> None:
        # The negative control behind the `executable-route` mandatory id: a
        # declared mechanism nothing runs must be named, or the id would be a
        # claim about a checker that has never been seen to refuse anything.
        self.assertEqual(
            ["EXECUTABLE_ROUTE_HOLLOW:demo:scripts/unreached.py"],
            check_skill_bundles.scan_hollow_execution_routes(
                "demo", ["scripts/unreached.py"], "no tests mention it", "no runner row"
            ),
        )
        self.assertEqual(
            [],
            check_skill_bundles.scan_hollow_execution_routes(
                "demo", ["scripts/unreached.py"], "import unreached", "no runner row"
            ),
        )

    def test_tree_digest_changes_when_bytes_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            path = temp / "file.txt"
            path.write_text("a", encoding="utf-8")
            first = tree_digest(digest_entries(temp, regular_files(temp)))
            path.write_text("b", encoding="utf-8")
            second = tree_digest(digest_entries(temp, regular_files(temp)))
            self.assertNotEqual(first, second)

    def test_freeze_source_requires_exact_commit_and_hashes_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            source = checkout / "skills" / "demo"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("demo\n", encoding="utf-8")
            lock = build_lock(
                checkout,
                "https://github.com/example/repo",
                "a" * 40,
                "skills/demo",
                "demo",
            )
            self.assertEqual("git", lock["source_kind"])
            self.assertEqual(1, len(lock["locked_files"]))
            self.assertEqual("skills/demo/SKILL.md", lock["locked_files"][0]["path"])

    def test_case_producer_must_match_the_declared_class_not_just_the_method_name(
        self,
    ) -> None:
        # The old check was `f"def {method}(" in concatenated_test_text`, which
        # a producer naming the wrong class -- but the right method name -- on
        # a different class in the same file would satisfy. This is the
        # negative control behind the `EVAL_CASE_PRODUCER_ABSENT` id: a
        # binding that claims a class it isn't actually defined on must be
        # named, not accepted because *some* class has a same-named method.
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            (skill_root / "tests").mkdir()
            (skill_root / "tests" / "test_demo.py").write_text(
                "class Other:\n"
                "    def test_thing(self) -> None:\n"
                "        pass\n"
                "\n"
                "class Real:\n"
                "    def test_other_thing(self) -> None:\n"
                "        pass\n",
                encoding="utf-8",
            )
            cases = [
                {"id": "wrong-class", "test": "test_demo.Real.test_thing"},
                {"id": "right-class", "test": "test_demo.Other.test_thing"},
            ]
            errors = check_skill_bundles.scan_case_producers(
                "demo", skill_root, ["tests/test_demo.py"], cases
            )
            self.assertEqual(
                ["EVAL_CASE_PRODUCER_ABSENT:demo:wrong-class:test_demo.Real.test_thing"],
                errors,
            )

    def test_roles_claim_without_a_declaration_fails(self) -> None:
        # ed3c/skill-concerns#62 goal 3. BUILD/SHADOW were prose: a skill could
        # name either role and never say what that role is bound to. These are
        # the planted fixtures behind the two diagnostics - a doc that claims a
        # role with no `Roles:` block at all, and a block that names both roles
        # but drops the reader-only clause and the S0/S1/S2 severities.
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            (skill_root / "SKILL.md").write_text(
                "# demo\n\nThe SHADOW agent watches the run.\n", encoding="utf-8"
            )
            (skill_root / "README.md").write_text(
                "# demo\n\nRoles: BUILD executes; SHADOW supervises.\n", encoding="utf-8"
            )
            self.assertEqual(
                [
                    "SKILL_ROLES_DECLARATION_ABSENT:demo:SKILL.md",
                    "SKILL_ROLES_DECLARATION_INCOMPLETE:demo:README.md:reader-only,S0,S1,S2",
                ],
                check_skill_bundles.scan_role_declarations("demo", skill_root),
            )

    def test_roles_scan_is_silent_on_a_skill_that_claims_no_role(self) -> None:
        # Positive control: the check must not demand a roles block from every
        # skill, only from one that claims a role. `MODULE_NAME_SHADOWED` is a
        # diagnostic id, not a role claim, and must not trip the word match.
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            (skill_root / "SKILL.md").write_text(
                "# demo\n\nRefuses on MODULE_NAME_SHADOWED.\n", encoding="utf-8"
            )
            self.assertEqual(
                [], check_skill_bundles.scan_role_declarations("demo", skill_root)
            )

    # ----------------------------------------------------------------------
    # Dual-standard conformance (ed3c/skill-concerns#74).
    #
    # One planted negative per assertion. A sweep that has only ever been run
    # against a conformant tree is a single arrival: every green it produced is
    # unfalsified, not verified.

    def write_validator(self, skill_root: Path, clauses: str | None) -> None:
        (skill_root / "scripts").mkdir(parents=True, exist_ok=True)
        body = "" if clauses is None else f"SKILL_MD_CLAUSES = {clauses}\n"
        (skill_root / "scripts" / "validate_demo.py").write_text(
            f'"""demo validator."""\n{body}', encoding="utf-8"
        )

    def test_validator_absent_from_the_declared_execution_paths_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            self.assertEqual(
                ["SKILL_VALIDATOR_ABSENT:demo"],
                check_skill_bundles.scan_validator_contract(
                    "demo", skill_root, ["scripts/driver.py"], ["skills/demo/tests"]
                ),
            )

    def test_validator_not_wired_into_the_runner_row_fails(self) -> None:
        # Present and count-tied, but nothing runs it: a validator no row names
        # is a checker that has never refused anything in this repository.
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            self.write_validator(skill_root, '("Only section",)')
            (skill_root / "SKILL.md").write_text(
                "# demo\n\n## Only section\n\nbody\n", encoding="utf-8"
            )
            self.assertEqual(
                ["SKILL_VALIDATOR_UNWIRED:demo:scripts/validate_demo.py",
                 "SKILL_TESTS_UNWIRED:demo"],
                check_skill_bundles.scan_validator_contract(
                    "demo", skill_root, ["scripts/validate_demo.py"], ["unrelated"]
                ),
            )
            self.assertEqual(
                ["SKILL_CHECKS_ROW_ABSENT:demo"],
                check_skill_bundles.scan_validator_contract(
                    "demo", skill_root, ["scripts/validate_demo.py"], None
                ),
            )

    def test_hollowed_skill_md_breaks_the_count_tie(self) -> None:
        # The assertion issue #74 names by example: a validator can stay green
        # while the SKILL.md it exists for loses a section, because nothing
        # counted the sections.
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            row = ["skills/demo/scripts/validate_demo.py", "skills/demo/tests"]
            self.write_validator(skill_root, '("Decision boundary", "Hard constraints")')
            entrypoint = skill_root / "SKILL.md"
            entrypoint.write_text(
                "# demo\n\n## Decision boundary\n\na\n\n## Hard constraints\n\nb\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                check_skill_bundles.scan_validator_contract(
                    "demo", skill_root, ["scripts/validate_demo.py"], row
                ),
            )
            entrypoint.write_text("# demo\n\n## Decision boundary\n\na\n", encoding="utf-8")
            self.assertEqual(
                ["SKILL_CLAUSE_COUNT_UNTIED:demo:declared=2:observed=1"
                 ":drift=Hard constraints"],
                check_skill_bundles.scan_validator_contract(
                    "demo", skill_root, ["scripts/validate_demo.py"], row
                ),
            )
            self.write_validator(skill_root, None)
            self.assertEqual(
                ["SKILL_CLAUSE_CONTRACT_ABSENT:demo:scripts/validate_demo.py"],
                check_skill_bundles.scan_validator_contract(
                    "demo", skill_root, ["scripts/validate_demo.py"], row
                ),
            )

    def test_fenced_headings_do_not_count_as_sections(self) -> None:
        # Several SKILL.md files carry ```text diagrams whose lines start with
        # `#`. Counting those would tie the contract to illustration bytes.
        self.assertEqual(
            ["Real"],
            check_skill_bundles.markdown_sections(
                "## Real\n\n```text\n## Not a section\n```\n"
            ),
        )

    def test_runner_rows_are_read_per_skill_not_as_one_blob(self) -> None:
        # A substring search over the whole runner would read a path as wired
        # for every Skill, including the one whose row does not contain it.
        with tempfile.TemporaryDirectory() as directory:
            runner = Path(directory) / "run_all.py"
            runner.write_text(
                'DISCOVER = ("-m", "unittest")\n'
                "SKILL_CHECKS = {\n"
                '    "a": (("skills/a/scripts/validate_a.py",), (*DISCOVER, "skills/a/tests")),\n'
                '    "b": ((*DISCOVER, "skills/b/tests"),),\n'
                "}\n",
                encoding="utf-8",
            )
            rows = check_skill_bundles.runner_rows(runner)
            self.assertEqual({"a", "b"}, set(rows))
            self.assertIn("skills/a/scripts/validate_a.py", rows["a"])
            self.assertNotIn("skills/a/scripts/validate_a.py", rows["b"])

    def test_stale_admission_stamp_fails(self) -> None:
        root = self.scratch_copy()
        self.assertEqual(
            [], check_skill_bundles.scan_admission_stamp(
                "control-backup", root, root / "skills" / "control-backup"
            )
        )
        (root / "skills" / "control-backup" / "SKILL.md").write_text(
            "hollowed\n", encoding="utf-8"
        )
        self.assertEqual(
            ["ADMISSION_STAMP_STALE:control-backup"],
            check_skill_bundles.scan_admission_stamp(
                "control-backup", root, root / "skills" / "control-backup"
            ),
        )
        (root / "admissions" / "control-backup.json").unlink()
        self.assertEqual(
            ["ADMISSION_STAMP_ABSENT:control-backup"],
            check_skill_bundles.scan_admission_stamp(
                "control-backup", root, root / "skills" / "control-backup"
            ),
        )

    def test_negative_arm_sharing_the_positive_producer_fails(self) -> None:
        # The nonconformance this atom found and fixed: a FAIL case pointing at
        # the assertion a PASS case already names is one execution counted as
        # two arms, and the receipt then carries a control id whose only
        # measurement is the positive control.
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            (skill_root / "evals").mkdir()
            cases = [
                {"id": "positive", "expected": "PASS", "test": "m.C.test_selftest"},
                {"id": "planted", "expected": "FAIL", "test": "m.C.test_selftest"},
                {"id": "own-arm", "expected": "FAIL", "test": "m.C.test_defused"},
            ]
            self.assertEqual(
                ["CAMPAIGN_ARM_SHARES_PRODUCER:demo:planted:m.C.test_selftest"],
                check_skill_bundles.scan_campaign(
                    "demo", skill_root, "evals/cases.json", cases
                ),
            )
            self.assertEqual(
                ["CAMPAIGN_DIRECTORY_ABSENT:demo:cases.json"],
                check_skill_bundles.scan_campaign("demo", skill_root, "cases.json", []),
            )

    def test_receipt_entry_without_a_ground_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory)
            (skill_root / "scripts").mkdir()
            (skill_root / "scripts" / "driver.py").write_text("x\n", encoding="utf-8")

            def write(evidence: dict) -> None:
                (skill_root / "receipts.json").write_text(
                    json.dumps({"schema_version": 1, "evidence": evidence}),
                    encoding="utf-8",
                )

            write({"bare": {"claim": "something happened"}})
            self.assertEqual(
                ["RECEIPT_ENTRY_UNGROUNDED:demo:bare"],
                check_skill_bundles.scan_receipt_producers("demo", skill_root),
            )
            write({"gone": {"claim": "c", "producer": "scripts/deleted.py"}})
            self.assertEqual(
                ["RECEIPT_PRODUCER_ABSENT:demo:gone:scripts/deleted.py"],
                check_skill_bundles.scan_receipt_producers("demo", skill_root),
            )
            write({"escape": {"claim": "c", "producer": "../../etc/passwd"}})
            self.assertEqual(
                ["RECEIPT_PRODUCER_ESCAPES_SKILL:demo:escape:../../etc/passwd"],
                check_skill_bundles.scan_receipt_producers("demo", skill_root),
            )
            write(
                {
                    "replayed": {"claim": "c", "producer": "scripts/driver.py"},
                    "cited": {"claim": "c", "refs": ["ed3c/skill-concerns#74"]},
                    "host": {"claim": "c", "producer": "HOST_OBSERVED"},
                }
            )
            self.assertEqual(
                [], check_skill_bundles.scan_receipt_producers("demo", skill_root)
            )

    def test_unregistered_skill_row_in_the_collection_documents_fails(self) -> None:
        root = self.scratch_copy()
        self.assertEqual(
            [], check_skill_bundles.scan_collection_rows(
                "control-backup", "domain-rich", root
            )
        )
        self.assertEqual(
            ["SKILL_INDEX_ROW_KIND_DRIFT:control-backup:procedure-rich"],
            check_skill_bundles.scan_collection_rows(
                "control-backup", "procedure-rich", root
            ),
        )
        index = root / "skills" / "README.md"
        index.write_text(
            "\n".join(
                line
                for line in index.read_text(encoding="utf-8").splitlines()
                if "`control-backup`" not in line
            ),
            encoding="utf-8",
        )
        agents = root / "skills" / "AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8").replace(
                ", skills/control-backup/AGENTS.md", ""
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            [
                "SKILL_COLLECTION_ROW_ABSENT:control-backup",
                "SKILL_INDEX_ROW_ABSENT:control-backup:0",
            ],
            check_skill_bundles.scan_collection_rows(
                "control-backup", "domain-rich", root
            ),
        )

    def test_missing_pstack_birth_artifact_fails(self) -> None:
        root = self.scratch_copy()
        self.assertEqual([], check_skill_bundles.scan_birth_artifacts(root))

        receipt = root / check_skill_bundles.BIRTH_PROVE_ONCE
        document = json.loads(receipt.read_text(encoding="utf-8"))
        document["run"]["exit_code"] = 1
        document["run"]["report_sha256"] = "not-a-digest"
        receipt.write_text(json.dumps(document, indent=2), encoding="utf-8")

        feature_map = root / check_skill_bundles.BIRTH_FEATURE_MAP
        map_document = json.loads(feature_map.read_text(encoding="utf-8"))
        map_document["transitions"] = []
        feature_map.write_text(json.dumps(map_document, indent=2), encoding="utf-8")

        doctor = root / check_skill_bundles.BIRTH_DOCTOR
        doctor.write_text(
            doctor.read_text(encoding="utf-8").replace(
                "class StampRefused", "class Whatever"
            ),
            encoding="utf-8",
        )

        self.assertEqual(
            [
                "BIRTH_FEATURE_MAP_INCOMPLETE:transitions",
                "BIRTH_DOCTOR_INCOMPLETE:class StampRefused",
                "BIRTH_PROVE_ONCE_NOT_GREEN:1",
                "BIRTH_PROVE_ONCE_DIGEST_INVALID",
            ],
            check_skill_bundles.scan_birth_artifacts(root),
        )
        doctor.unlink()
        self.assertIn(
            f"BIRTH_DOCTOR_ABSENT:{check_skill_bundles.BIRTH_DOCTOR}",
            check_skill_bundles.scan_birth_artifacts(root),
        )

    def test_current_skill_bundles_pass(self) -> None:
        self.assertEqual([], check_skill_bundles.check(ROOT))

    def test_current_admissions_pass(self) -> None:
        self.assertEqual([], check_admissions.check(ROOT))

    def scratch_copy(self) -> Path:
        temp = tempfile.TemporaryDirectory(prefix="authoring-command-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name) / "repo"
        shutil.copytree(
            ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__")
        )
        return root.resolve()

    def test_authoring_command_accepts_the_per_skill_producer(self) -> None:
        # PR #43 changed both this check and the value it reads in one landing
        # and was graded by the *old* trusted copy, which still demanded
        # "python3 scripts/run_all.py": five AUTHORING_COMMAND_INVALID rows.
        # Accepting both values is the landing that makes the split possible.
        root = self.scratch_copy()
        receipt = root / "admissions" / "control-backup.json"
        data = json.loads(receipt.read_text(encoding="utf-8"))

        for command in (
            "python3 scripts/run_all.py",
            "python3 skills/control-backup/scripts/gen_admission.py",
        ):
            with self.subTest(authoring_command=command):
                data["authoring_command"] = command
                receipt.write_text(
                    json.dumps(data, indent=2) + "\n", encoding="utf-8"
                )
                self.assertEqual([], check_admissions.check(root))

        data["authoring_command"] = "python3 scripts/make_it_green.py"
        receipt.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(
            ["AUTHORING_COMMAND_INVALID:control-backup"],
            check_admissions.check(root),
        )


class CureAuthorizationTests(unittest.TestCase):
    """The BUILD cure-authorization rule, ed3c/skill-concerns#93.

    The two carriers exercise this decision end to end in their own selftests.
    What is asserted here is the decision itself in both directions, and the
    single-implementation claim the issue makes -- a claim no carrier can prove
    about itself.
    """

    def test_the_canonical_case_is_refused_and_names_the_rule(self) -> None:
        refusal = cure_authorization.refuse(
            "skills/demo", cure_authorization.COPY_NEAREST_RATCHET, None
        )
        self.assertIsNotNone(refusal)
        self.assertEqual(cure_authorization.DIAGNOSTIC, refusal.diagnostic)
        self.assertIn("ratchet", refusal.detail)
        self.assertIn("ed3c/skill-concerns#93", refusal.detail)

    def test_the_same_bytes_with_an_adjudication_are_admitted(self) -> None:
        self.assertIsNone(
            cure_authorization.refuse(
                "skills/demo",
                cure_authorization.COPY_NEAREST_RATCHET,
                dict(cure_authorization.ADJUDICATED_AUTHORIZATION),
            )
        )

    def test_a_proposal_with_no_enforcement_shape_needs_no_authorization(self) -> None:
        """The rule binds enforcement shapes, not every regenerated byte."""
        self.assertIsNone(
            cure_authorization.refuse("skills/demo", '{"regenerated": true}', None)
        )

    def test_a_shadow_detection_is_refused_by_name(self) -> None:
        refusal = cure_authorization.refuse(
            "skills/demo",
            cure_authorization.COPY_NEAREST_RATCHET,
            {"kind": "shadow-detection", "ref": "ed3c/skill-concerns#93"},
        )
        self.assertIn("SHADOW detections never authorize", refusal.detail)

    def test_a_ref_whose_form_contradicts_its_kind_is_refused(self) -> None:
        for kind, ref in (
            ("discriminating-measurement", "operator:2026-09-01:a conversation"),
            ("operator-adjudication", "ed3c/skill-concerns#93"),
            ("hand-wave", "ed3c/skill-concerns#93"),
        ):
            with self.subTest(kind=kind):
                self.assertIsNotNone(
                    cure_authorization.refuse(
                        "skills/demo",
                        cure_authorization.COPY_NEAREST_RATCHET,
                        {"kind": kind, "ref": ref},
                    )
                )

    def test_the_judges_garbage_operator_ref_is_refused(self) -> None:
        """ed3c/skill-concerns#103, the exact bytes the wave-19 judge ran.

        Three garbage refs passed `check_method_claims` on landed main because
        the form was any date plus any non-empty text. This is the one the judge
        recorded, and the refusal has to name what is missing rather than say
        the record is bad.
        """
        refusal = cure_authorization.refuse(
            "skills/demo",
            cure_authorization.COPY_NEAREST_RATCHET,
            {"kind": "operator-adjudication", "ref": cure_authorization.VIBES_REF},
            tree=ROOT,
        )
        self.assertIsNotNone(refusal)
        self.assertIn("names no pinned subject", refusal.detail)
        self.assertIn("names no adjudication artifact", refusal.detail)

    def test_an_operator_ref_resolving_to_a_real_artifact_is_admitted(self) -> None:
        """The planted negative arm: an issue-grounded ref passes.

        Its subject exists in this tree, its own ref repeats that subject, and
        the artifact is a provider ref the cadence sweep re-resolves. Nothing
        about the tightening refuses a real adjudication.
        """
        self.assertIsNone(
            cure_authorization.refuse(
                "skills/demo",
                cure_authorization.COPY_NEAREST_RATCHET,
                {
                    "kind": "operator-adjudication",
                    "ref": "operator:2026-09-01:scripts/cure_authorization.py - the rule",
                    "subject": "scripts/cure_authorization.py",
                    "adjudication": {"issue": "ed3c/skill-concerns#93"},
                },
                tree=ROOT,
            )
        )

    def test_an_expired_inline_adjudication_is_refused_as_expired(self) -> None:
        """Lapsed and malformed are different states and must not read alike."""
        base = {
            "kind": "operator-adjudication",
            "ref": "operator:2026-09-01:scripts/cure_authorization.py - the rule",
            "subject": "scripts/cure_authorization.py",
        }
        today = date(2026, 9, 2)
        expired = cure_authorization.authorization_errors(
            {**base, "adjudication": {"record": "the operator said so", "expires": "2026-01-01"}},
            tree=ROOT,
            today=today,
        )
        self.assertTrue(any("expired on 2026-01-01" in error for error in expired))
        self.assertEqual(
            [],
            cure_authorization.authorization_errors(
                {**base, "adjudication": {"record": "the operator said so", "expires": "2026-12-01"}},
                tree=ROOT,
                today=today,
            ),
        )
        self.assertEqual(
            [],
            cure_authorization.authorization_errors(
                {
                    **base,
                    "adjudication": {
                        "record": "the operator said so",
                        "re_resolve": "every maintain cadence pass",
                    },
                },
                tree=ROOT,
                today=today,
            ),
        )
        undated = cure_authorization.authorization_errors(
            {**base, "adjudication": {"record": "the operator said so"}},
            tree=ROOT,
            today=today,
        )
        self.assertTrue(any("neither an expiry nor a" in error for error in undated))
        self.assertFalse(any("expired" in error for error in undated))

    def test_an_operator_subject_that_resolves_to_nothing_is_refused(self) -> None:
        """A pinned subject is pinned to bytes, or it pins nothing."""
        errors = cure_authorization.authorization_errors(
            {
                "kind": "operator-adjudication",
                "ref": "operator:2026-09-01:scripts/a_file_nobody_wrote.py - the rule",
                "subject": "scripts/a_file_nobody_wrote.py",
                "adjudication": {"issue": "ed3c/skill-concerns#93"},
            },
            tree=ROOT,
        )
        self.assertTrue(any("does not exist in the tree" in error for error in errors))

    def test_every_carrier_passes_the_tree_an_operator_subject_resolves_against(self) -> None:
        """Absence of a tree is refused, not silently graded shape-only.

        The weaker reading is exactly the free exit this tightening closed, so
        it must not be reachable by forgetting an argument at a call site.
        """
        errors = cure_authorization.authorization_errors(
            {
                "kind": "operator-adjudication",
                "ref": "operator:2026-09-01:scripts/cure_authorization.py - the rule",
                "subject": "scripts/cure_authorization.py",
                "adjudication": {"issue": "ed3c/skill-concerns#93"},
            }
        )
        self.assertTrue(any("no tree was given" in error for error in errors))
        modules = [
            ROOT / "scripts" / "maintain_skills.py",
            ROOT / "skills" / "arrival-engineering" / "scripts" / "audit_islands.py",
            ROOT / "skills" / "red-team" / "scripts" / "shadow_driver.py",
        ]
        for path in modules:
            with self.subTest(carrier=path.name):
                calls = [
                    node
                    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "refuse"
                ]
                self.assertTrue(calls)
                for call in calls:
                    self.assertIn(
                        "tree", [keyword.arg for keyword in call.keywords]
                    )

    def test_a_verb_whose_subject_is_the_shape_always_needs_an_authorization(self) -> None:
        """`always=True` is for a carrier whose whole verb legislates."""
        self.assertIsNotNone(
            cure_authorization.refuse("catalogue", '{"id": "quiet"}', None, always=True)
        )
        self.assertIsNone(
            cure_authorization.refuse(
                "catalogue",
                '{"id": "quiet"}',
                dict(cure_authorization.ADJUDICATED_AUTHORIZATION),
                always=True,
            )
        )

    def test_only_one_module_implements_the_refusal(self) -> None:
        """No second copy of the check, read out of the bytes rather than trusted.

        Both carriers must reach the rule, and the diagnostic literal must
        exist in exactly one implementation - a carrier that spelled the
        diagnostic itself would be a second reading of the rule wearing the
        same name.
        """
        modules = sorted((ROOT / "scripts").glob("*.py")) + sorted(
            (ROOT / "skills").glob("*/scripts/*.py")
        )
        spellers = [
            path.relative_to(ROOT).as_posix()
            for path in modules
            if f'"{cure_authorization.DIAGNOSTIC}"' in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(["scripts/cure_authorization.py"], spellers)

        callers = [
            path.relative_to(ROOT).as_posix()
            for path in modules
            if "cure_authorization.refuse(" in path.read_text(encoding="utf-8")
        ]
        # Hand-listed on purpose, against this repository's usual preference for
        # a glob: a new BUILD carrier reaching the rule is exactly the change a
        # reviewer must see, so it lands as an edit here rather than as a row
        # that quietly appears.
        self.assertEqual(
            [
                "scripts/maintain_skills.py",
                "skills/arrival-engineering/scripts/audit_islands.py",
                "skills/red-team/scripts/shadow_driver.py",
            ],
            callers,
        )

    def test_the_adjudication_is_carried_in_agents_md(self) -> None:
        """Delete the ruling from AGENTS.md and this reds."""
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("ed3c/skill-concerns#93", text)
        self.assertIn("BUILD may only carry adjudicated cures", text)
        for shape in cure_authorization.SHAPES:
            with self.subTest(shape=shape):
                self.assertIn(shape, text)


if __name__ == "__main__":
    unittest.main()
