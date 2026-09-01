#!/usr/bin/env python3
"""Validate admitted Skill anatomy and concern declarations."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
from typing import Any, Iterable

from common import REPO_ROOT, load_json, print_result, safe_repo_path


REQUIRED_MANIFEST_KEYS = {
    "schema_version",
    "name",
    "version",
    "kind",
    "entrypoint",
    "portable_core_paths",
    "domain_paths",
    "execution_paths",
    "test_paths",
    "eval_inventory",
    "read_route",
    "forbidden_domain_literals",
    "shared_contracts",
}
REQUIRED_FILES = {"AGENTS.md", "README.md", "SKILL.md", "skill.json"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# The maintain loop's two halves (ed3c/skill-concerns#62): BUILD is the half
# allowed to propose edits, SHADOW is reader-only and reports at severities
# S0/S1/S2. A skill that names either half is making a claim about who may
# write during its own operation, so both halves, the reader-only clause, and
# the severities must be on the page rather than assumed by the reader.
# `\bSHADOW\b` deliberately does not match `MODULE_NAME_SHADOWED`.
ROLE_CLAIM = re.compile(r"\b(?:BUILD|SHADOW)\b")
ROLE_DECLARATION_TOKENS = ("BUILD", "SHADOW", "reader-only", "S0", "S1", "S2")
ROLE_DOCUMENTS = ("SKILL.md", "README.md")


def roles_block(text: str) -> str | None:
    """The paragraph opened by a `Roles:` line, or None when there is none.

    Paragraph-scoped rather than whole-document: a document-wide token search
    would be satisfied by `BUILD` in one section and `S1` in an unrelated one,
    which is not a declaration of anything.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if "Roles:" not in line:
            continue
        block = [line]
        for following in lines[index + 1 :]:
            if not following.strip():
                break
            block.append(following)
        return "\n".join(block)
    return None


def scan_role_declarations(
    name: str, skill_root: Path, documents: Iterable[str] = ROLE_DOCUMENTS
) -> list[str]:
    """A skill claiming BUILD or SHADOW must declare both, in one Roles block."""
    errors: list[str] = []
    for relative in documents:
        path = skill_root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if not ROLE_CLAIM.search(text):
            continue
        block = roles_block(text)
        if block is None:
            errors.append(f"SKILL_ROLES_DECLARATION_ABSENT:{name}:{relative}")
            continue
        missing = [token for token in ROLE_DECLARATION_TOKENS if token not in block]
        if missing:
            errors.append(
                f"SKILL_ROLES_DECLARATION_INCOMPLETE:{name}:{relative}:{','.join(missing)}"
            )
    return errors


def parse_skill_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, [f"SKILL_FRONTMATTER_ABSENT:{path}"]
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return {}, [f"SKILL_FRONTMATTER_UNTERMINATED:{path}"]
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    if not values.get("name"):
        errors.append(f"SKILL_FRONTMATTER_NAME_MISSING:{path}")
    if "description" not in values:
        errors.append(f"SKILL_FRONTMATTER_DESCRIPTION_MISSING:{path}")
    return values, errors


def scan_forbidden_literals(
    skill_root: Path, paths: list[str], literals: list[str]
) -> list[str]:
    errors: list[str] = []
    for relative in paths:
        path = skill_root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for literal in literals:
            if isinstance(literal, str) and literal.lower() in text:
                errors.append(f"DOMAIN_LITERAL_IN_PORTABLE_CORE:{relative}:{literal}")
    return errors


def scan_hollow_execution_routes(
    name: str, execution: list[str], test_text: str, runner_text: str
) -> list[str]:
    """Every declared mechanism must be reachable from tests or the root runner."""
    return [
        f"EXECUTABLE_ROUTE_HOLLOW:{name}:{relative}"
        for relative in execution
        if Path(relative).stem not in test_text and relative not in runner_text
    ]


def _qualified_test_methods(skill_root: Path, tests: list[str]) -> set[tuple[str, str, str]]:
    """(module, class, method) for every test method declared under `tests`.

    Parsed per file with `ast`, not by grepping concatenated text: a producer
    string names a specific module.Class.method, and a `def name(` substring
    search would count a same-named method on an unrelated class as a match.
    """
    found: set[tuple[str, str, str]] = set()
    for relative in tests:
        path = skill_root / relative
        if not path.is_file():
            continue
        module = Path(relative).stem
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found.add((module, node.name, child.name))
    return found


def scan_case_producers(
    name: str, skill_root: Path, tests: list[str], cases: list[Any]
) -> list[str]:
    """Every eval case's `test` field must name an assertion that exists.

    Independent of `admission_stamp`: this proves the binding is declared in
    the Skill's own test files; the stamper proves the binding ran green
    (ed3c/skill-concerns#40).
    """
    errors: list[str] = []
    qualified = _qualified_test_methods(skill_root, tests)
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = case.get("id")
        producer = case.get("test")
        if not isinstance(producer, str) or producer.count(".") != 2:
            errors.append(f"EVAL_CASE_PRODUCER_INVALID:{name}:{case_id}")
            continue
        module, cls, method = producer.split(".")
        if (module, cls, method) not in qualified:
            errors.append(f"EVAL_CASE_PRODUCER_ABSENT:{name}:{case_id}:{producer}")
    return errors


def _path_list(
    manifest: dict[str, Any],
    key: str,
    skill_root: Path,
    errors: list[str],
    require_file: bool = True,
) -> list[str]:
    values = manifest.get(key)
    if not isinstance(values, list):
        errors.append(f"MANIFEST_PATH_LIST_INVALID:{key}")
        return []
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            errors.append(f"MANIFEST_PATH_INVALID:{key}:{value!r}")
            continue
        candidate = Path(value)
        if candidate.is_absolute() or ".." in candidate.parts:
            errors.append(f"MANIFEST_PATH_ESCAPES_SKILL:{key}:{value}")
            continue
        path = skill_root / candidate
        if require_file and not path.is_file():
            errors.append(f"MANIFEST_PATH_ABSENT:{key}:{value}")
        result.append(value)
    if len(result) != len(set(result)):
        errors.append(f"MANIFEST_PATH_DUPLICATE:{key}")
    return result


def check(root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    try:
        registry = load_json(root / "registry.json")
    except ValueError as exc:
        return [str(exc)]

    policy = registry.get("policy")
    if not isinstance(policy, dict):
        errors.append("REGISTRY_POLICY_INVALID")
        policy = {}
    allowed_kinds = policy.get("allowed_kinds", [])
    if not isinstance(allowed_kinds, list):
        errors.append("REGISTRY_ALLOWED_KINDS_INVALID")
        allowed_kinds = []

    rows = registry.get("skills")
    if not isinstance(rows, list):
        return errors + ["REGISTRY_SKILLS_NOT_LIST"]

    registered_paths: set[str] = set()
    registered_names: set[str] = set()
    skills_dir = root / "skills"
    actual_skill_dirs = {
        path.relative_to(root).as_posix()
        for path in skills_dir.iterdir()
        if path.is_dir()
    }

    runner_text = ""
    runner = root / "scripts" / "run_all.py"
    if runner.is_file():
        runner_text = runner.read_text(encoding="utf-8")

    for row in rows:
        if not isinstance(row, dict):
            errors.append("REGISTRY_SKILL_ROW_NOT_OBJECT")
            continue
        name = row.get("name")
        skill_path_value = row.get("path")
        kind = row.get("kind")
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
            errors.append(f"REGISTRY_SKILL_NAME_INVALID:{name}")
            continue
        if name in registered_names:
            errors.append(f"REGISTRY_SKILL_NAME_DUPLICATE:{name}")
        registered_names.add(name)
        if not isinstance(skill_path_value, str):
            errors.append(f"REGISTRY_SKILL_PATH_INVALID:{name}")
            continue
        registered_paths.add(skill_path_value)
        try:
            skill_root = safe_repo_path(root, skill_path_value)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not skill_root.is_dir():
            errors.append(f"SKILL_DIRECTORY_ABSENT:{skill_path_value}")
            continue
        if skill_root.name != name:
            errors.append(f"SKILL_DIRECTORY_NAME_MISMATCH:{name}:{skill_root.name}")
        if kind not in allowed_kinds:
            errors.append(f"SKILL_KIND_INVALID:{name}:{kind}")

        for required in REQUIRED_FILES:
            if not (skill_root / required).is_file():
                errors.append(f"SKILL_REQUIRED_FILE_ABSENT:{name}:{required}")

        manifest_path = skill_root / "skill.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = load_json(manifest_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(manifest, dict):
            errors.append(f"MANIFEST_NOT_OBJECT:{name}")
            continue
        missing_keys = REQUIRED_MANIFEST_KEYS - set(manifest)
        for key in sorted(missing_keys):
            errors.append(f"MANIFEST_KEY_ABSENT:{name}:{key}")
        if manifest.get("schema_version") != 1:
            errors.append(f"MANIFEST_SCHEMA_VERSION:{name}")
        if manifest.get("name") != name:
            errors.append(f"MANIFEST_NAME_MISMATCH:{name}:{manifest.get('name')}")
        if manifest.get("kind") != kind:
            errors.append(f"MANIFEST_KIND_MISMATCH:{name}:{manifest.get('kind')}")
        if manifest.get("entrypoint") != "SKILL.md":
            errors.append(f"MANIFEST_ENTRYPOINT_INVALID:{name}")

        frontmatter, frontmatter_errors = parse_skill_frontmatter(skill_root / "SKILL.md")
        errors.extend(frontmatter_errors)
        errors.extend(scan_role_declarations(name, skill_root))
        if frontmatter.get("name") != name:
            errors.append(
                f"SKILL_FRONTMATTER_NAME_MISMATCH:{name}:{frontmatter.get('name')}"
            )

        portable = _path_list(manifest, "portable_core_paths", skill_root, errors)
        domain = _path_list(manifest, "domain_paths", skill_root, errors)
        execution = _path_list(manifest, "execution_paths", skill_root, errors)
        tests = _path_list(manifest, "test_paths", skill_root, errors)
        read_route = _path_list(manifest, "read_route", skill_root, errors)
        eval_inventory = manifest.get("eval_inventory")
        if not isinstance(eval_inventory, str):
            errors.append(f"EVAL_INVENTORY_INVALID:{name}")
        else:
            _path_list(
                {"eval_inventory_list": [eval_inventory]},
                "eval_inventory_list",
                skill_root,
                errors,
            )

        if kind == "procedure-rich" and domain:
            errors.append(f"PROCEDURE_RICH_DOMAIN_PATHS_FORBIDDEN:{name}")
        if kind == "domain-rich" and not domain:
            errors.append(f"DOMAIN_RICH_DOMAIN_PATHS_REQUIRED:{name}")
        if kind == "composed" and (not portable or not domain):
            errors.append(f"COMPOSED_CONCERNS_INCOMPLETE:{name}")

        literals = manifest.get("forbidden_domain_literals")
        if not isinstance(literals, list) or any(
            not isinstance(item, str) or not item for item in literals
        ):
            errors.append(f"FORBIDDEN_DOMAIN_LITERALS_INVALID:{name}")
            literals = []
        errors.extend(scan_forbidden_literals(skill_root, portable, literals))

        shared_contracts = manifest.get("shared_contracts")
        if not isinstance(shared_contracts, list) or not shared_contracts:
            errors.append(f"SHARED_CONTRACTS_INVALID:{name}")
        else:
            for relative in shared_contracts:
                if not isinstance(relative, str):
                    errors.append(f"SHARED_CONTRACT_PATH_INVALID:{name}:{relative!r}")
                    continue
                candidate = Path(relative)
                if candidate.is_absolute():
                    errors.append(f"SHARED_CONTRACT_PATH_ABSOLUTE:{name}:{relative}")
                    continue
                contract = (skill_root / candidate).resolve()
                repository_root = root.resolve()
                if contract != repository_root and repository_root not in contract.parents:
                    errors.append(f"SHARED_CONTRACT_PATH_ESCAPES_REPOSITORY:{name}:{relative}")
                    continue
                if not contract.is_file():
                    errors.append(f"SHARED_CONTRACT_ABSENT:{name}:{relative}")

        if not read_route or read_route[:3] != ["AGENTS.md", "README.md", "SKILL.md"]:
            errors.append(f"SKILL_READ_ROUTE_INVALID:{name}")

        nested_agents = [
            path
            for path in skill_root.rglob("AGENTS.md")
            if path != skill_root / "AGENTS.md"
        ]
        for path in nested_agents:
            errors.append(
                f"SKILL_AGENT_DOCUMENT_NESTED:{path.relative_to(root).as_posix()}"
            )

        test_text = "\n".join(
            (skill_root / relative).read_text(encoding="utf-8")
            for relative in tests
            if (skill_root / relative).is_file()
        )
        errors.extend(
            scan_hollow_execution_routes(name, execution, test_text, runner_text)
        )

        if isinstance(eval_inventory, str) and (skill_root / eval_inventory).is_file():
            try:
                inventory = load_json(skill_root / eval_inventory)
            except ValueError as exc:
                errors.append(str(exc))
            else:
                cases = inventory.get("cases") if isinstance(inventory, dict) else None
                if not isinstance(cases, list) or not cases:
                    errors.append(f"EVAL_CASES_EMPTY:{name}")
                else:
                    ids: set[str] = set()
                    positive = False
                    negative = False
                    for case in cases:
                        if not isinstance(case, dict):
                            errors.append(f"EVAL_CASE_NOT_OBJECT:{name}")
                            continue
                        case_id = case.get("id")
                        expected = case.get("expected")
                        if not isinstance(case_id, str) or not case_id:
                            errors.append(f"EVAL_CASE_ID_INVALID:{name}")
                        elif case_id in ids:
                            errors.append(f"EVAL_CASE_ID_DUPLICATE:{name}:{case_id}")
                        else:
                            ids.add(case_id)
                        if expected == "PASS":
                            positive = True
                        elif expected == "FAIL":
                            negative = True
                        else:
                            errors.append(
                                f"EVAL_CASE_EXPECTED_INVALID:{name}:{case_id}:{expected}"
                            )
                    errors.extend(scan_case_producers(name, skill_root, tests, cases))
                    if not positive:
                        errors.append(f"EVAL_POSITIVE_CONTROL_ABSENT:{name}")
                    if not negative:
                        errors.append(f"EVAL_NEGATIVE_CONTROL_ABSENT:{name}")

    for path in sorted(actual_skill_dirs - registered_paths):
        errors.append(f"UNREGISTERED_SKILL_DIRECTORY:{path}")
    for path in sorted(registered_paths - actual_skill_dirs):
        errors.append(f"REGISTERED_SKILL_DIRECTORY_ABSENT:{path}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    return print_result("skill-bundles", check(args.root.resolve()))


if __name__ == "__main__":
    raise SystemExit(main())
