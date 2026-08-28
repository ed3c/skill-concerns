from __future__ import annotations

import copy
import json
from pathlib import Path
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

    def test_current_skill_bundles_pass(self) -> None:
        self.assertEqual([], check_skill_bundles.check(ROOT))

    def test_current_admissions_pass(self) -> None:
        self.assertEqual([], check_admissions.check(ROOT))


if __name__ == "__main__":
    unittest.main()
