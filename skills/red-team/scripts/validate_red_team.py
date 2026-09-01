#!/usr/bin/env python3
"""Deterministic validator for the red-team bundle: schemas, ties, and one scan.

Every check here is either a SCHEMA this bundle owns or a TIE between two
places that must agree, so a hollowed document reds instead of describing a
mechanism that is no longer there:

  clauses    <-> kernel entries              (count-tied, one kernel per clause)
  clauses    <-> receipts evidence ids       (every clause cited, every id bound)
  catalogue  <-> shadow_driver.EXPERIMENTS   (by id, both ways)
  Diagnostics prose <-> shadow_driver.DIAGNOSTICS (by name, both ways)
  receipts.json <-> gen_receipts.render(catalogue) (byte-identical; hand edits red)
  catalogue lifecycle <-> its own gate and stock-sweep references

Three schemas are owned here rather than by the driver that emits them, so the
thing that JUDGES a record is not the thing that WROTE it: `finding_errors`,
`signal_errors`, and `completeness_reasons`. The driver imports the first two
and refuses to emit a record they reject.

`FORBIDDEN_SURFACE` is the reader property as a tested surface rather than a
promise: the driver's bytes are scanned for provider-mutating verbs, the same
way the sibling observer bundle tests its own no-write claim. A planted
mutating call in a fixture copy turns it red.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

CLAUSE_RE = re.compile(r"^## (R\d+)\. ", re.M)
KERNEL_RE = re.compile(r"^- (K\d+) ", re.M)
REQUIRED_FIELDS = ("- Signal:", "- Action:", "- Why:", "- evidence:")
BACKTICKED = re.compile(r"`([^`]+)`")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ROLE_TOKENS = ("BUILD", "SHADOW", "reader-only", "S0", "S1", "S2")

# SKILL.md's `## ` headings, in order. `scripts/check_skill_bundles.py` reads
# this tuple out of these bytes (parsed, never imported) and compares it to the
# document's own headings, so a clause deleted from SKILL.md reds against a
# file the deletion never touched.
SKILL_MD_CLAUSES = (
    "The catalogue - pinned bytes, front-loaded as the whole job",
    "Clause form",
    "R1. The catalogue is bytes at a commit, never rules improvised into a prompt",
    "R2. A catalogue hit is a hypothesis until its recipe runs",
    "R3. Reader-only against the subject; experiments run in throwaway clones",
    "R4. A finding is a record with an experiment block, not prose with a number",
    "R5. Escalation is one signal to the dispatcher, from a bounded list of classes",
    "R6. The catalogue grows only by adjudicated verdict and shrinks only by a landed gate",
    "R7. The instrument reports its own failure to bend the curve",
    "Diagnostics",
    "Knowledge placement",
    "Non-claims",
)

# --------------------------------------------------------------------------
# schemas this bundle owns

FINDING_FIELDS = (
    "id",
    "catalogue_class",
    "subject",
    "experiment",
    "verdict",
    "both_directions",
)
VERDICTS = ("CONFIRMED", "REFUTED", "INCONCLUSIVE")
# A command is a command. Prose in the slot where a command belongs is the
# exact malformity ed3c/skill-concerns#94 names, so the grammar is a closed
# list of verbs rather than "a non-empty string".
COMMAND_RE = re.compile(r"^(?:python3|git|gh|grep|jq|diff|sha256sum|ls) \S")

SIGNAL_FIELDS = ("severity", "catalogue_class", "subject", "reason", "finding")
SIGNAL_SEVERITIES = ("S1", "S2")
# The bounded list, and it lives in the contract rather than in a judgement.
# A signal citing anything else is a validator error, not a louder signal.
URGENT_CLASSES = ("irreversible-action-in-progress", "runaway-resource-burn")
# A signal carries no instructions and no patches. These keys are what an
# instruction would arrive as, so their presence is the refusal.
SIGNAL_FORBIDDEN_FIELDS = ("instructions", "patch", "diff", "command", "fix")

# Provider-mutating verbs. The driver may never contain one.
FORBIDDEN_SURFACE = (
    re.compile(r"\bgh\s+issue\s+(?:create|edit|comment|close|delete|reopen)\b"),
    re.compile(r"\bgh\s+pr\s+(?:create|edit|merge|close|comment|ready)\b"),
    re.compile(r"\bgh\s+api\b[^\n]*(?:-X|--method)\s*(?:PATCH|POST|PUT|DELETE)"),
    re.compile(r"(?:PATCH|POST|PUT|DELETE)[^\n]*api\.github\.com"),
    re.compile(r"\burllib\.request\.Request\b[^\n]*method\s*="),
)

# --------------------------------------------------------------------------
# the consumer's issue-admission completeness shape, mirrored deliberately
#
# Provenance: ed3c/noodles `issue_contract.py` - `sections()`,
# `required_section_reasons()`, `completeness_reasons()` - read 2026-09-02.
# This is a MIRROR and says so: that gate lives in another repository, this one
# takes no dependency on it, and clause A4 of `arrival-engineering` is why the
# mirror names exactly which functions it copies instead of claiming to be the
# gate. Deliberately NOT mirrored, because they need the consumer's own system
# specification and provider readback and cannot be decided from a body alone:
# the noodles-requirement id resolution, and the dependency-state derivation.
#
# The load-bearing detail is the stripping: fenced blocks and HTML comments are
# removed BEFORE sections are cut, so a section whose only content is a fenced
# block arrives at that gate empty. That is why `render_demonstration` emits no
# fence, and the round-trip fixture is what keeps the two facts tied.
FENCE_RE = re.compile(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$")
HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
SECTION_RE = re.compile(r"(?m)^##[ \t]+(?P<heading>\S[^\n]*?)[ \t]*$")
REQUIRED_SECTIONS = ("goal", "claim", "physical_acceptance", "non_claims")
RATIONALE_SECTION = "physical_trigger"
RATIONALE_PREFIX = "why_"
NON_CASE_SECTION = "non_case"
DEMONSTRATION_SECTION = "observer_demonstration"
ACCEPTANCE_OBLIGATIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("positive control", ("positive control", "positive:", "positive/planted")),
    ("planted-negative control", ("planted-negative", "planted negative", "negative control")),
    ("direct readback", ("readback",)),
    ("zero-residue readback", ("residue", "cleanup")),
)

NEIGHBOURS = {
    "spatial-loop-grounded": "issues clause verdicts over supervised conduct",
    "context-closure-engineering": "compiles and checks one bounded context projection",
    "dynamic-workflow": "classifies runtime liveness of dispatch lanes",
}
# The fourth neighbour is not in this tree yet (ed3c/skill-concerns#75 has not
# landed). Absence gets its own exit rather than a silent pass: the boundary
# term must be on the page, and the check says the bytes were unavailable.
ABSENT_NEIGHBOUR = "shadow-architect"


def finding_errors(record: Any) -> list[str]:
    """Everything wrong with one finding record, or an empty list."""
    if not isinstance(record, dict):
        return [f"finding is not a record: {record!r}"]
    errors = [f"missing field {field!r}" for field in FINDING_FIELDS if field not in record]
    if errors:
        return errors
    subject = record["subject"]
    if not isinstance(subject, dict) or not subject.get("path"):
        errors.append("subject names no path")
    elif not HEX64.fullmatch(str(subject.get("sha256", ""))):
        errors.append(f"subject {subject['path']} is not bound to an exact sha256")
    experiment = record["experiment"]
    if not isinstance(experiment, dict):
        return errors + ["experiment is not a block"]
    commands = experiment.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("experiment block carries no command sequence")
    else:
        for command in commands:
            if not isinstance(command, str) or not COMMAND_RE.match(command.strip()):
                errors.append(f"prose where a command belongs: {command!r}")
    for field in ("expected", "observed"):
        if not str(experiment.get(field) or "").strip():
            errors.append(f"experiment block has no {field}")
    if record["verdict"] not in VERDICTS:
        errors.append(f"verdict {record['verdict']!r} is outside {list(VERDICTS)}")
    if not str(record["both_directions"] or "").strip():
        errors.append("both-directions status is absent")
    return errors


def signal_errors(record: Any) -> list[str]:
    """Everything wrong with one escalation signal, or an empty list."""
    if not isinstance(record, dict):
        return [f"signal is not a record: {record!r}"]
    errors = [f"missing field {field!r}" for field in SIGNAL_FIELDS if field not in record]
    present = [field for field in SIGNAL_FORBIDDEN_FIELDS if field in record]
    if present:
        errors.append(
            f"a signal carries no instructions and no patches; found {present}"
        )
    if errors:
        return errors
    if record["severity"] not in SIGNAL_SEVERITIES:
        errors.append(f"severity {record['severity']!r} is outside {list(SIGNAL_SEVERITIES)}")
    if record["catalogue_class"] not in URGENT_CLASSES:
        errors.append(
            f"signal cites {record['catalogue_class']!r}, which is outside the bounded "
            f"urgent list {list(URGENT_CLASSES)}"
        )
    if "\n" in str(record["reason"]) or not str(record["reason"]).strip():
        errors.append("reason must be one non-empty line")
    if not str(record["finding"] or "").strip():
        errors.append("signal references no finding")
    return errors


def sections(body: str) -> dict[str, str]:
    text = HTML_COMMENT_RE.sub("", FENCE_RE.sub("", body or ""))
    matches = list(SECTION_RE.finditer(text))
    parsed: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        key = re.sub(r"[^a-z0-9]+", "_", match.group("heading").lower()).strip("_")
        parsed[key] = text[match.end() : end].strip()
    return parsed


def completeness_reasons(body: str) -> list[str]:
    """The consumer's admission dry-run over a candidate issue body."""
    parsed = sections(body)
    reasons = [
        f"issue body has no '## {name.replace('_', ' ')}' section"
        for name in REQUIRED_SECTIONS
        if not (parsed.get(name) or "").strip()
    ]
    if not any(
        (parsed.get(name) or "").strip()
        for name in parsed
        if name == RATIONALE_SECTION or name.startswith(RATIONALE_PREFIX)
    ):
        reasons.append(
            "issue body has no '## Physical trigger' section and no admitted "
            "'Why ...' rationale heading"
        )
    if not (parsed.get(NON_CASE_SECTION) or "").strip():
        reasons.append("issue body has no '## Non-case' section")
    acceptance = (parsed.get("physical_acceptance") or "").lower()
    for label, tokens in ACCEPTANCE_OBLIGATIONS:
        if not any(token in acceptance for token in tokens):
            reasons.append(f"'## Physical acceptance' names no {label} obligation")
    if not (parsed.get(DEMONSTRATION_SECTION) or "").strip():
        reasons.append(
            "'## Observer demonstration' carries no authored assertion after fenced "
            "blocks and HTML comments are stripped"
        )
    return reasons


# --------------------------------------------------------------------------
# ties


def clause_bodies(text: str) -> dict[str, str]:
    parts = CLAUSE_RE.split(text)
    return {
        parts[index]: parts[index + 1].split("\n## ", 1)[0]
        for index in range(1, len(parts), 2)
    }


def section_text(text: str, heading: str) -> str:
    marker = f"\n## {heading}\n"
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def check_clauses(text: str, errors: list[str]) -> dict[str, str]:
    bodies = clause_bodies(text)
    if not bodies:
        errors.append("SKILL.md declares no R-clauses")
    for clause_id, body in bodies.items():
        for field in REQUIRED_FIELDS:
            if field not in body:
                errors.append(f"{clause_id}: trigger form incomplete, missing {field!r}")
    return bodies


def check_kernel(skill_root: Path, bodies: dict[str, str], errors: list[str]) -> None:
    path = skill_root / "references" / "portable-falsification-kernel.md"
    if not path.is_file():
        errors.append("L0 kernel references/portable-falsification-kernel.md missing")
        return
    text = path.read_text(encoding="utf-8")
    if "L0 procedural" not in text:
        errors.append("L0 kernel does not declare itself the procedural layer")
    kernels = KERNEL_RE.findall(text)
    if len(kernels) != len(bodies):
        errors.append(
            f"kernel/clause count mismatch: {len(kernels)} kernels vs {len(bodies)} clauses"
        )
    if len(kernels) != len(set(kernels)):
        errors.append("duplicate kernel ids")


def check_experiment_tie(catalogue: dict, errors: list[str]) -> None:
    """Every class has an experiment, every experiment has a class.

    Imported lazily: the driver imports this module for its schemas, so a
    module-level import here would be a cycle. By call time both modules are
    fully initialised whichever one was entered first.
    """
    import shadow_driver  # noqa: PLC0415

    declared = {
        entry["id"]
        for entry in catalogue.get("classes", [])
        if isinstance(entry, dict) and entry.get("id")
    }
    for missing in sorted(declared - set(shadow_driver.EXPERIMENTS)):
        errors.append(f"catalogue class {missing!r} has no experiment in the toolkit")
    for extra in sorted(set(shadow_driver.EXPERIMENTS) - declared):
        errors.append(f"toolkit experiment {extra!r} matches no catalogue class")
    for entry in catalogue.get("classes", []):
        named = (entry.get("falsification") or {}).get("experiment")
        if named != entry.get("id"):
            errors.append(
                f"catalogue class {entry.get('id')!r} names experiment {named!r}"
            )


def check_diagnostic_tie(text: str, errors: list[str]) -> None:
    import shadow_driver  # noqa: PLC0415

    body = section_text(text, "Diagnostics")
    if not body:
        errors.append("SKILL.md has no Diagnostics section")
        return
    documented = {
        token for token in BACKTICKED.findall(body) if re.fullmatch(r"[A-Z][A-Z_]+", token)
    }
    for missing in sorted(set(shadow_driver.DIAGNOSTICS) - documented):
        errors.append(f"Diagnostics section omits a diagnostic the driver emits: {missing}")
    for extra in sorted(documented - set(shadow_driver.DIAGNOSTICS)):
        errors.append(f"Diagnostics section names a diagnostic the driver cannot emit: {extra}")


def check_catalogue(catalogue: dict, errors: list[str]) -> None:
    entries = catalogue.get("classes")
    if not isinstance(entries, list) or not entries:
        errors.append("catalogue carries no classes")
        return
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("catalogue class is not an object")
            continue
        class_id = entry.get("id")
        if not isinstance(class_id, str) or not class_id:
            errors.append("catalogue class has no id")
            continue
        if class_id in seen:
            errors.append(f"catalogue class id duplicated: {class_id}")
        seen.add(class_id)
        for key in ("title", "signal"):
            if not str(entry.get(key) or "").strip():
                errors.append(f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: no {key}")
        provenance = entry.get("provenance")
        if not isinstance(provenance, dict) or not provenance.get("receipts"):
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: no provenance receipt grounds "
                "this class, so nothing says which wave found it"
            )
        elif not str(provenance.get("why") or "").strip():
            errors.append(f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: provenance carries no why")
        falsification = entry.get("falsification")
        recipe = (falsification or {}).get("recipe") if isinstance(falsification, dict) else None
        if not isinstance(recipe, list) or not recipe or not all(
            isinstance(step, str) and COMMAND_RE.match(step.strip()) for step in recipe
        ):
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: falsification recipe is not a "
                "runnable command sequence"
            )
        elif not str(falsification.get("both_directions") or "").strip():
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: recipe names no both-directions arm"
            )
        status = entry.get("status")
        if status not in {"active", "gated"}:
            errors.append(f"catalogue class {class_id!r} status {status!r} is neither active nor gated")
            continue
        gate = str(entry.get("gate_ref") or "").strip()
        if status == "gated" and not gate:
            errors.append(
                f"CATALOGUE_GATE_REFERENCE_ABSENT:{class_id}: gated with no gate to point at"
            )
        if status == "active" and gate:
            errors.append(
                f"CATALOGUE_CLASS_GATED_BUT_ACTIVE:{class_id}: a landed gate is named "
                f"({gate.split(':')[0]}) while the class is still sampled"
            )
        if not str(entry.get("stock_sweep_ref") or "").strip():
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: no stock-sweep reference, so "
                "whether the existing instances were dispositioned is archaeology"
            )


def check_ledger(skill_root: Path, errors: list[str]) -> None:
    path = skill_root / "domain" / "run-ledger.json"
    if not path.is_file():
        errors.append("domain/run-ledger.json missing")
        return
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if not str(ledger.get("append_only") or "").strip():
        errors.append("run ledger does not declare itself append-only")
    records = ledger.get("records")
    if not isinstance(records, list):
        errors.append("run ledger carries no records list")
        return
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"run record {position} is not an object")
            continue
        for field in (
            "run_id",
            "wave",
            "boundary",
            "classes_sampled",
            "hits",
            "novel_class_candidates",
            "judge_gaps",
            "duplicate_blocks",
        ):
            if field not in record:
                errors.append(f"run record {position} has no {field!r}")


def check_forbidden_surface(path: Path, errors: list[str]) -> None:
    """Scan the driver's bytes for a provider-mutating verb.

    Quotes, brackets and commas are blanked per line first, so an argv list
    (`["gh", "issue", "create"]`) reads the same as a shell string - a scan
    that only matched the shell spelling would be blind to the form the code
    actually uses, which is the blind-observer class inside the instrument that
    names it.

    Line-scoped, and that is a real ceiling: an argv split across source lines
    would pass. The upgrade is an ast walk over call nodes; it is not here
    because every mutating call this repository writes fits on one line.
    """
    if not path.is_file():
        errors.append(f"DRIVER_SURFACE_FORBIDDEN:{path.name}: driver absent")
        return
    normalized = "\n".join(
        re.sub(r"[\"'\[\],]", " ", line) for line in path.read_text(encoding="utf-8").splitlines()
    )
    for pattern in FORBIDDEN_SURFACE:
        match = pattern.search(normalized)
        if match:
            errors.append(
                f"DRIVER_SURFACE_FORBIDDEN:{path.name}: provider-mutating call "
                f"{' '.join(match.group(0).split())!r}; this driver never files, "
                "comments, or merges"
            )


def check_evidence(bodies: dict[str, str], receipts: dict, errors: list[str]) -> None:
    evidence = receipts.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        errors.append("receipts.json evidence table missing or empty")
        return
    for key, entry in sorted(evidence.items()):
        if not isinstance(entry, dict) or not entry.get("refs"):
            errors.append(f"receipts.json evidence {key!r} has no refs")
        elif not str(entry.get("claim") or "").strip():
            errors.append(f"receipts.json evidence {key!r} has no claim")
    cited: set[str] = set()
    for clause_id, body in bodies.items():
        match = re.search(r"^- evidence: (.+)$", body, re.M)
        if not match:
            continue
        for token in (item.strip() for item in match.group(1).split(",")):
            cited.add(token)
            if token not in evidence:
                errors.append(f"{clause_id}: evidence id {token!r} not in receipts.json")
    for key in sorted(set(evidence) - cited):
        errors.append(f"receipts.json evidence {key!r} is bound to no clause")


def check_receipts_are_produced(skill_root: Path, catalogue: dict, errors: list[str]) -> None:
    from gen_receipts import ReceiptRefused, render  # noqa: PLC0415

    path = skill_root / "receipts.json"
    if not path.is_file():
        errors.append("receipts.json missing")
        return
    try:
        produced = render(catalogue)
    except ReceiptRefused as exc:
        # The producer refusing IS the finding: a catalogue whose classes carry
        # no resolvable ref cannot author receipts at all, and reporting that as
        # a validator error keeps the whole sweep readable instead of raising
        # out of the middle of it.
        errors.append(str(exc))
        return
    if path.read_text(encoding="utf-8") != produced:
        errors.append(
            "receipts.json is not what gen_receipts.py produces from the catalogue - "
            "regenerate it with its producer; a hand-edited receipt is laundering even "
            "when the edit would be factually right"
        )


def check_roles(skill_root: Path, errors: list[str]) -> None:
    for relative in ("SKILL.md", "README.md"):
        path = skill_root / relative
        if not path.is_file():
            errors.append(f"{relative} missing")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        block = ""
        for index, line in enumerate(lines):
            if "Roles:" in line:
                collected = [line]
                for following in lines[index + 1 :]:
                    if not following.strip():
                        break
                    collected.append(following)
                block = "\n".join(collected)
                break
        if not block:
            errors.append(f"{relative} has no Roles: declaration block")
            continue
        for token in ROLE_TOKENS:
            if token not in block:
                errors.append(f"{relative} Roles block omits {token!r}")


def check_boundaries(repo_root: Path, text: str, errors: list[str]) -> None:
    """The differential is the verb, and it must be grep-verifiable on the page.

    A neighbour whose bytes are not in this tree is reported as unavailable
    rather than as agreement: unresolvable and unreachable are different states.
    """
    for name in NEIGHBOURS:
        if name not in text:
            errors.append(f"Non-claims does not name the neighbour it is not: {name}")
        elif not (repo_root / "skills" / name).is_dir():
            errors.append(f"neighbour {name} named but absent from this tree")
    if ABSENT_NEIGHBOUR not in text:
        errors.append(
            f"the fourth neighbour {ABSENT_NEIGHBOUR} is unadmitted and must still be "
            "named, with its issue, rather than silently omitted"
        )


def validate(skill_root: Path, repo_root: Path | None = None) -> list[str]:
    repo_root = repo_root or skill_root.parents[1]
    errors: list[str] = []
    skill_md = skill_root / "SKILL.md"
    catalogue_path = skill_root / "domain" / "catalogue.json"
    if not skill_md.is_file():
        return ["SKILL.md missing"]
    if not catalogue_path.is_file():
        return ["domain/catalogue.json missing"]
    text = skill_md.read_text(encoding="utf-8")
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))

    bodies = check_clauses(text, errors)
    check_kernel(skill_root, bodies, errors)
    check_experiment_tie(catalogue, errors)
    check_diagnostic_tie(text, errors)
    check_catalogue(catalogue, errors)
    check_ledger(skill_root, errors)
    check_forbidden_surface(skill_root / "scripts" / "shadow_driver.py", errors)
    check_roles(skill_root, errors)
    check_boundaries(repo_root, text, errors)
    check_receipts_are_produced(skill_root, catalogue, errors)
    if "Non-claims" not in text:
        errors.append("Non-claims section missing")

    receipts_path = skill_root / "receipts.json"
    if receipts_path.is_file():
        check_evidence(
            bodies, json.loads(receipts_path.read_text(encoding="utf-8")), errors
        )
    return errors


# --------------------------------------------------------------------------
# selftest: every tie reds when the side it ties to is hollowed


def selftest() -> int:
    real = Path(__file__).resolve().parents[1]
    repo_root = real.parents[1]
    checks: list[tuple[str, bool, str]] = []
    scratch = Path(tempfile.mkdtemp(prefix="red-team-validate-selftest-"))

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append((name, passed, detail))

    def fresh() -> Path:
        copy = scratch / f"copy{len(list(scratch.iterdir()))}"
        shutil.copytree(real, copy, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return copy

    def mutate(name: str, apply, needle: str) -> None:
        copy = fresh()
        apply(copy)
        errors = validate(copy, repo_root)
        record(name, any(needle in error for error in errors), f"errors={errors[:3]}")

    def edit_catalogue(copy: Path, change) -> None:
        path = copy / "domain" / "catalogue.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        change(body)
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

    try:
        record(
            "positive_control_unmutated_copy_passes",
            not validate(fresh(), repo_root),
            f"errors={validate(fresh(), repo_root)[:3]}",
        )

        def drop_kernel(copy: Path) -> None:
            path = copy / "references" / "portable-falsification-kernel.md"
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            path.write_text(
                "".join(line for line in lines if not line.startswith("- K7 ")),
                encoding="utf-8",
            )

        mutate("dropped_kernel_entry_breaks_the_count_tie", drop_kernel, "count mismatch")

        def strip_provenance(copy: Path) -> None:
            edit_catalogue(
                copy, lambda body: body["classes"][0].pop("provenance")
            )

        mutate(
            "class_without_provenance_reds",
            strip_provenance,
            "CATALOGUE_ENTRY_UNGROUNDED:blind-observer",
        )

        def prose_recipe(copy: Path) -> None:
            def change(body):
                body["classes"][1]["falsification"]["recipe"] = [
                    "read the receipts file and think about whether the exit is earned"
                ]

            edit_catalogue(copy, change)

        mutate(
            "class_whose_recipe_is_prose_reds",
            prose_recipe,
            "falsification recipe is not a runnable command sequence",
        )

        def gated_without_gate(copy: Path) -> None:
            edit_catalogue(
                copy,
                lambda body: body["classes"][5].__setitem__("gate_ref", None),
            )

        mutate(
            "gated_class_without_a_gate_reference_reds",
            gated_without_gate,
            "CATALOGUE_GATE_REFERENCE_ABSENT:shape-copying",
        )

        def active_with_a_gate(copy: Path) -> None:
            edit_catalogue(
                copy,
                lambda body: body["classes"][5].__setitem__("status", "active"),
            )

        mutate(
            "active_class_with_a_landed_gate_reds",
            active_with_a_gate,
            "CATALOGUE_CLASS_GATED_BUT_ACTIVE:shape-copying",
        )

        def strip_stock_sweep(copy: Path) -> None:
            edit_catalogue(
                copy, lambda body: body["classes"][2].__setitem__("stock_sweep_ref", "")
            )

        mutate(
            "class_without_a_stock_sweep_reference_reds",
            strip_stock_sweep,
            "no stock-sweep reference",
        )

        def plant_a_mutating_call(copy: Path) -> None:
            path = copy / "scripts" / "shadow_driver.py"
            path.write_text(
                path.read_text(encoding="utf-8")
                + '\n\ndef file_it(number: int) -> None:\n'
                '    subprocess.run(["gh", "issue", "comment", str(number)])\n',
                encoding="utf-8",
            )

        mutate(
            "planted_provider_mutation_reds_the_forbidden_surface_scan",
            plant_a_mutating_call,
            "DRIVER_SURFACE_FORBIDDEN",
        )

        def hand_edit_receipts(copy: Path) -> None:
            path = copy / "receipts.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            body["evidence"]["free-exit"]["claim"] = "a nicer sentence"
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate("hand_edited_receipts_red", hand_edit_receipts, "not what gen_receipts.py produces")

        def drop_a_diagnostic(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "`SIGNAL_CLASS_UNBOUNDED`", "SIGNAL_CLASS_UNBOUNDED"
                ),
                encoding="utf-8",
            )

        mutate(
            "undocumented_diagnostic_reds",
            drop_a_diagnostic,
            "Diagnostics section omits a diagnostic",
        )

        def unname_a_neighbour(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("dynamic-workflow", "that other one"),
                encoding="utf-8",
            )

        mutate(
            "unnamed_neighbour_reds",
            unname_a_neighbour,
            "does not name the neighbour it is not",
        )

        # Schema controls: a malformed finding, an out-of-list signal, and a
        # demonstration block that the consumer's gate would read as empty.
        good = {
            "id": "F01",
            "catalogue_class": "free-exit",
            "subject": {"path": "receipts/a.json", "sha256": "0" * 64},
            "experiment": {
                "commands": ["grep -c HOST_OBSERVED receipts/a.json"],
                "expected": "some entry is refused",
                "observed": "all entries take the exit",
            },
            "verdict": "CONFIRMED",
            "both_directions": "positive: the all-exit fixture; negative: a grounded file",
        }
        record("well_formed_finding_passes_the_schema", not finding_errors(good), "")
        record(
            "finding_without_observed_reds",
            any(
                "no observed" in error
                for error in finding_errors({**good, "experiment": {**good["experiment"], "observed": ""}})
            ),
            "",
        )
        record(
            "prose_where_a_command_belongs_reds",
            any(
                "prose where a command belongs" in error
                for error in finding_errors(
                    {**good, "experiment": {**good["experiment"], "commands": ["have a look at the file"]}}
                )
            ),
            "",
        )
        record(
            "signal_outside_the_urgent_list_reds",
            any(
                "outside the bounded" in error
                for error in signal_errors(
                    {
                        "severity": "S2",
                        "catalogue_class": "free-exit",
                        "subject": "receipts/a.json",
                        "reason": "the exit is free",
                        "finding": "F01",
                    }
                )
            ),
            "",
        )
        record(
            "signal_carrying_a_patch_reds",
            any(
                "no instructions and no patches" in error
                for error in signal_errors(
                    {
                        "severity": "S2",
                        "catalogue_class": URGENT_CLASSES[0],
                        "subject": "ops/",
                        "reason": "a force-push is in flight",
                        "finding": "F01",
                        "patch": "--- a\n+++ b\n",
                    }
                )
            ),
            "",
        )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    record("no_residue_outlives_the_run", not scratch.exists(), f"scratch={scratch}")

    for name, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    failed = [name for name, passed, _ in checks if not passed]
    if failed:
        print(f"selftest FAILED: {failed}")
        return 1
    print("selftest OK: every tie reds when the side it ties to is hollowed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    errors = validate(args.skill_root.resolve())
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: red-team clause, kernel, catalogue, schema, surface and receipt ties intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
