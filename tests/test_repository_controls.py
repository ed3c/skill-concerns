from __future__ import annotations

import copy
import json
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


if __name__ == "__main__":
    unittest.main()
