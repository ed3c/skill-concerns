#!/usr/bin/env python3
"""Validate admitted Skill anatomy and concern declarations."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
from typing import Any, Iterable

from common import (
    REPO_ROOT,
    digest_entries,
    load_json,
    print_result,
    regular_files,
    safe_repo_path,
    tree_digest,
)


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

# --------------------------------------------------------------------------
# Dual-standard conformance (ed3c/skill-concerns#74)
#
# Everything below asserts the SHAPE a bundle must carry, per skill, generically.
# Before this, eight of those shapes were author memory: an admission issue could
# enumerate them, and nothing re-read the enumeration. What the sweep cannot
# prove is method honesty -- that the interview behind a feature map was
# faithful, that a campaign arm measured anything. Those stay with campaigns,
# planted negatives and wave monitors, exactly as issue #74 scopes them.
#
# Trust boundary: `verify.yml` runs THIS file from the default branch against
# the candidate tree as data. Nothing here imports or executes a candidate
# module -- `scripts/run_all.py` and each Skill's validator are read as bytes
# and parsed with `ast`, never imported.
VALIDATOR_PREFIX = "validate_"

# The declared contract every Skill validator carries so the count tie is
# generic: a tuple of the exact `## ` section headings of that Skill's SKILL.md.
# Read out of the validator's own bytes, so the gate has no per-skill list to go
# stale, and a hollowed SKILL.md reds against a tuple the hollowing never
# touched.
CLAUSE_CONTRACT = "SKILL_MD_CLAUSES"

# The explicit exit a receipts entry takes when its evidence is a one-time host
# observation nothing in this repository replays. An honest declaration, never a
# waiver: it keeps "no producer" distinguishable from "producer ran green".
HOST_OBSERVED = "HOST_OBSERVED"

MARKDOWN_FENCE = re.compile(r"^\s*```")
MARKDOWN_SECTION = re.compile(r"^##\s+(.+?)\s*$")

# pstack's birth triple, by shape. These are repository-level artifacts: one
# feature map for the admission capability, one Doctor that refuses before it
# drives, one prove-once receipt for the first live run. A per-skill copy of
# each does not exist and inventing six would be fabrication, not conformance.
#
# The Doctor named here is the stamper's refusing preflight. The cadence sweep
# owns a `doctor()` of its own and is the more obvious reading, but it is
# N-class by contract -- nothing on the gate path may name it, and its own suite
# reds on the module name appearing in any script under `scripts/`. A gate that
# required the sweep to exist would be a gate consuming an N-class reader, which
# is exactly the coupling that guard refuses. See AGENTS.md, "Content freshness".
BIRTH_FEATURE_MAP = "docs/features/skill-admission/feature-map.json"
BIRTH_DOCTOR = "scripts/admission_stamp.py"
BIRTH_DOCTOR_SHAPE = ("class StampRefused", "REFUSAL")
BIRTH_PROVE_ONCE = "ops/first-run-receipt.json"
FEATURE_MAP_SHAPE = ("feature", "actor", "states", "transitions", "observables")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


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


def markdown_sections(text: str) -> list[str]:
    """The `## ` headings of a Markdown document, fenced blocks excluded.

    Fenced blocks are skipped because several SKILL.md files carry ```text
    diagrams whose lines start with `#`; counting those would tie the contract
    to illustration bytes instead of to the document's clause structure.
    """
    sections: list[str] = []
    fenced = False
    for line in text.splitlines():
        if MARKDOWN_FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = MARKDOWN_SECTION.match(line)
        if match:
            sections.append(match.group(1))
    return sections


def declared_clauses(path: Path) -> list[str] | None:
    """`SKILL_MD_CLAUSES` read out of a validator's bytes, or None if absent.

    Parsed with `ast`, never imported: in CI this file is trusted code reading a
    candidate module, and importing the candidate would execute it.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    except (OSError, SyntaxError):
        return None
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else []
        )
        if not any(
            isinstance(target, ast.Name) and target.id == CLAUSE_CONTRACT
            for target in targets
        ):
            continue
        try:
            value = ast.literal_eval(node.value)
        except ValueError:
            return None
        if isinstance(value, (list, tuple)) and all(
            isinstance(item, str) for item in value
        ):
            return list(value)
        return None
    return None


def runner_rows(runner: Path) -> dict[str, list[str]]:
    """Skill name -> every string literal in that Skill's `SKILL_CHECKS` row.

    Structural rather than a substring search over the whole runner: a path that
    appears anywhere in the file would otherwise read as "wired" for every
    Skill, including the one whose row does not contain it. Starred names such
    as `*DISCOVER` contribute nothing here, which is why the tests directory is
    asserted from the row's own literal rather than from the shared tuple.
    """
    rows: dict[str, list[str]] = {}
    try:
        tree = ast.parse(runner.read_text(encoding="utf-8"), filename=runner.name)
    except (OSError, SyntaxError):
        return rows
    for node in ast.walk(tree):
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else []
        )
        if not any(
            isinstance(target, ast.Name) and target.id == "SKILL_CHECKS"
            for target in targets
        ):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        for key, row in zip(node.value.keys, node.value.values):
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                rows[key.value] = [
                    child.value
                    for child in ast.walk(row)
                    if isinstance(child, ast.Constant) and isinstance(child.value, str)
                ]
    return rows


def scan_validator_contract(
    name: str, skill_root: Path, execution: list[str], row: list[str] | None
) -> list[str]:
    """Validator present, wired into the runner's row, and count-tied to SKILL.md.

    The tie is the whole point: a validator can be present and green while the
    SKILL.md it is supposed to be validating loses a clause, because nothing
    counted the clauses. `SKILL_MD_CLAUSES` is the Skill's own declaration of
    that count and of the identities behind it, so dropping a section reds
    against bytes the drop never touched.
    """
    errors: list[str] = []
    validators = sorted(
        relative
        for relative in execution
        if Path(relative).name.startswith(VALIDATOR_PREFIX)
    )
    if not validators:
        return [f"SKILL_VALIDATOR_ABSENT:{name}"]
    if len(validators) > 1:
        errors.append(f"SKILL_VALIDATOR_AMBIGUOUS:{name}:{','.join(validators)}")
    relative = validators[0]
    validator = skill_root / relative

    if row is None:
        errors.append(f"SKILL_CHECKS_ROW_ABSENT:{name}")
    else:
        if f"skills/{name}/{relative}" not in row:
            errors.append(f"SKILL_VALIDATOR_UNWIRED:{name}:{relative}")
        if f"skills/{name}/tests" not in row:
            errors.append(f"SKILL_TESTS_UNWIRED:{name}")

    if not validator.is_file():
        return errors + [f"SKILL_VALIDATOR_ABSENT:{name}:{relative}"]
    declared = declared_clauses(validator)
    if declared is None:
        return errors + [f"SKILL_CLAUSE_CONTRACT_ABSENT:{name}:{relative}"]
    entrypoint = skill_root / "SKILL.md"
    observed = (
        markdown_sections(entrypoint.read_text(encoding="utf-8"))
        if entrypoint.is_file()
        else []
    )
    if declared != observed:
        errors.append(
            f"SKILL_CLAUSE_COUNT_UNTIED:{name}:declared={len(declared)}:"
            f"observed={len(observed)}:"
            f"drift={','.join(sorted(set(declared) ^ set(observed))) or 'ORDER'}"
        )
    return errors


def scan_admission_stamp(name: str, root: Path, skill_root: Path) -> list[str]:
    """The stamp exists and was taken against the bytes that are here now.

    Independent of `check_admissions`, which reaches its own digest comparison
    only for a registry row complete enough to get that far: a row missing its
    `admission` key short-circuits there and the stamp is never looked at. Here
    the subject is the directory, so a stampless or stale bundle is named
    whatever the registry says about it.
    """
    stamp_path = root / "admissions" / f"{name}.json"
    if not stamp_path.is_file():
        return [f"ADMISSION_STAMP_ABSENT:{name}"]
    try:
        stamp = load_json(stamp_path)
        actual = tree_digest(digest_entries(root, regular_files(skill_root)))
    except ValueError as exc:
        return [str(exc)]
    if not isinstance(stamp, dict):
        return [f"ADMISSION_STAMP_NOT_OBJECT:{name}"]
    if stamp.get("skill") != name:
        return [f"ADMISSION_STAMP_SKILL_MISMATCH:{name}:{stamp.get('skill')}"]
    if stamp.get("skill_tree_sha256") != actual:
        return [f"ADMISSION_STAMP_STALE:{name}"]
    return []


def scan_campaign(
    name: str, skill_root: Path, eval_inventory: str, cases: list[Any]
) -> list[str]:
    """The eval campaign is a directory, and its negative arm is its own arm.

    A `FAIL` case pointing at the same assertion a `PASS` case points at is not
    a second arm: one execution is being counted twice, and the receipt then
    carries a control id whose only measurement is the positive control. That is
    the shape `context-closure-engineering`'s `task-packet-unbounded` had
    (ed3c/skill-concerns#74).

    Live-agent behavioral campaigns stay outside this sweep by
    `docs/behavioral-eval-protocol.md`; what is asserted here is the hermetic
    campaign every Skill carries.
    """
    errors: list[str] = []
    campaign = Path(eval_inventory).parent
    if campaign in (Path("."), Path("")) or not (skill_root / campaign).is_dir():
        errors.append(f"CAMPAIGN_DIRECTORY_ABSENT:{name}:{eval_inventory}")
    positive = {
        case.get("test")
        for case in cases
        if isinstance(case, dict) and case.get("expected") == "PASS"
    }
    for case in cases:
        if not isinstance(case, dict) or case.get("expected") != "FAIL":
            continue
        if case.get("test") in positive:
            errors.append(
                f"CAMPAIGN_ARM_SHARES_PRODUCER:{name}:{case.get('id')}:{case.get('test')}"
            )
    return errors


def scan_receipt_producers(name: str, skill_root: Path) -> list[str]:
    """Every receipts entry names its ground, and a named producer exists.

    Three grounds, because three exist and they are not interchangeable:

    - `producer`: a path under the Skill whose execution replays the claim
      (the L2 driver selftests do exactly this). A producer naming a path that
      is not there is worse than none -- it reads as grounded.
    - `refs`: provider or host pins, which the cadence sweep resolves at the
      provider or reports unreachable with a prerequisite.
    - `producer: "HOST_OBSERVED"`: the explicit exit for a one-time host
      observation with no repository producer at all. It is a declaration, not a
      pass: absence and a replayed claim must not look alike in the bytes, and
      before this an ungrounded entry looked exactly like a grounded one.
    """
    path = skill_root / "receipts.json"
    if not path.is_file():
        return []
    try:
        document = load_json(path)
    except ValueError as exc:
        return [str(exc)]
    evidence = document.get("evidence") if isinstance(document, dict) else None
    if not isinstance(evidence, dict) or not evidence:
        return [f"RECEIPT_EVIDENCE_EMPTY:{name}"]
    errors: list[str] = []
    for key in sorted(evidence):
        entry = evidence[key]
        if not isinstance(entry, dict):
            errors.append(f"RECEIPT_ENTRY_NOT_OBJECT:{name}:{key}")
            continue
        producer = entry.get("producer")
        refs = entry.get("refs")
        if producer == HOST_OBSERVED:
            continue
        if isinstance(producer, str) and producer:
            candidate = Path(producer)
            if candidate.is_absolute() or ".." in candidate.parts:
                errors.append(f"RECEIPT_PRODUCER_ESCAPES_SKILL:{name}:{key}:{producer}")
            elif not (skill_root / candidate).is_file():
                errors.append(f"RECEIPT_PRODUCER_ABSENT:{name}:{key}:{producer}")
        elif not (
            isinstance(refs, list)
            and any(isinstance(ref, str) and ref for ref in refs)
        ):
            errors.append(f"RECEIPT_ENTRY_UNGROUNDED:{name}:{key}")
    return errors


def scan_collection_rows(name: str, kind: Any, root: Path) -> list[str]:
    """The two collection documents carry this Skill's row.

    `check_agents_hops` proves the routing graph is closed; it does not prove
    the collection `AGENTS.md` is the document that routes to this Skill, and
    nothing at all read `skills/README.md`, which calls itself a reader's index
    and was therefore free to omit a bundle or misname its kind.
    """
    errors: list[str] = []
    agents = root / "skills" / "AGENTS.md"
    if not agents.is_file() or f"skills/{name}/AGENTS.md" not in agents.read_text(
        encoding="utf-8"
    ):
        errors.append(f"SKILL_COLLECTION_ROW_ABSENT:{name}")
    index = root / "skills" / "README.md"
    rows = (
        [
            line
            for line in index.read_text(encoding="utf-8").splitlines()
            if line.startswith("|") and f"`{name}`" in line
        ]
        if index.is_file()
        else []
    )
    if len(rows) != 1:
        errors.append(f"SKILL_INDEX_ROW_ABSENT:{name}:{len(rows)}")
    elif f"`{kind}`" not in rows[0]:
        errors.append(f"SKILL_INDEX_ROW_KIND_DRIFT:{name}:{kind}")
    return errors


def scan_birth_artifacts(root: Path) -> list[str]:
    """pstack's birth triple, by shape: feature map, Doctor, prove-once receipt.

    Shape only. That a feature map exists and declares states, transitions and
    observables is decidable from bytes; that the interview behind it was
    faithful is not, and this gate does not pretend otherwise.
    """
    errors: list[str] = []
    feature_map = root / BIRTH_FEATURE_MAP
    if not feature_map.is_file():
        errors.append(f"BIRTH_FEATURE_MAP_ABSENT:{BIRTH_FEATURE_MAP}")
    else:
        try:
            document = load_json(feature_map)
        except ValueError as exc:
            errors.append(str(exc))
            document = None
        if isinstance(document, dict):
            for key in FEATURE_MAP_SHAPE:
                if not document.get(key):
                    errors.append(f"BIRTH_FEATURE_MAP_INCOMPLETE:{key}")
        elif document is not None:
            errors.append("BIRTH_FEATURE_MAP_NOT_OBJECT")

    doctor = root / BIRTH_DOCTOR
    if not doctor.is_file():
        errors.append(f"BIRTH_DOCTOR_ABSENT:{BIRTH_DOCTOR}")
    else:
        text = doctor.read_text(encoding="utf-8")
        for token in BIRTH_DOCTOR_SHAPE:
            if token not in text:
                errors.append(f"BIRTH_DOCTOR_INCOMPLETE:{token}")

    prove_once = root / BIRTH_PROVE_ONCE
    if not prove_once.is_file():
        errors.append(f"BIRTH_PROVE_ONCE_ABSENT:{BIRTH_PROVE_ONCE}")
    else:
        try:
            receipt = load_json(prove_once)
        except ValueError as exc:
            return errors + [str(exc)]
        run = receipt.get("run") if isinstance(receipt, dict) else None
        if not isinstance(run, dict):
            errors.append("BIRTH_PROVE_ONCE_RUN_INVALID")
        else:
            if run.get("exit_code") != 0:
                errors.append(f"BIRTH_PROVE_ONCE_NOT_GREEN:{run.get('exit_code')}")
            if not HEX64.fullmatch(str(run.get("report_sha256", ""))):
                errors.append("BIRTH_PROVE_ONCE_DIGEST_INVALID")
    return errors


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
    rows_by_skill: dict[str, list[str]] = {}
    if runner.is_file():
        runner_text = runner.read_text(encoding="utf-8")
        rows_by_skill = runner_rows(runner)

    errors.extend(scan_birth_artifacts(root))

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
        errors.extend(
            scan_validator_contract(
                name, skill_root, execution, rows_by_skill.get(name)
            )
        )
        errors.extend(scan_admission_stamp(name, root, skill_root))
        errors.extend(scan_receipt_producers(name, skill_root))
        errors.extend(scan_collection_rows(name, kind, root))

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
                    errors.extend(
                        scan_campaign(name, skill_root, eval_inventory, cases)
                    )
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
