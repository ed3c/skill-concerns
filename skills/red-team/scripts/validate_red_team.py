#!/usr/bin/env python3
"""Deterministic validator for the red-team bundle: schemas, ties, and one scan.

Every check here is either a SCHEMA this bundle owns or a TIE between two
places that must agree, so a hollowed document reds instead of describing a
mechanism that is no longer there:

  clauses    <-> kernel entries              (count-tied, one kernel per clause)
  clauses    <-> receipts evidence ids       (every clause cited, every id bound)
  catalogue  <-> shadow_driver.EXPERIMENTS   (by id, both ways)
  Diagnostics prose <-> shadow_driver.DIAGNOSTICS (by name, both ways)
  receipts.json <-> gen_red_team_receipts.render(catalogue) (byte-identical; hand edits red)
  catalogue lifecycle <-> its own gate and stock-sweep references
  observation topology <-> the run ledger's subject vocabulary (one declaration)
  a station's runbook  <-> the document and the completion receipt it names
  a station's records  <-> the arrival row that tracks it (both directions)
  register rows        <-> every ceiling this bundle's own prose admits

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
import shlex
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

# The content digest and the role vocabulary are declared once, above `skills/`
# (ed3c/skill-concerns#112). This validator carried private copies of both while
# already putting `scripts/` on its own path; that path is resolved from THIS
# file, so under `check_receipt_provenance.py --root <candidate>` it lands in the
# candidate tree, not the trusted one. `skill.json` names
# `../../scripts/common.py` in `shared_contracts`, so the receipt binds the bytes
# these names come from.
from common import HEX64, ROLE_TOKENS, roles_block  # noqa: E402

CLAUSE_RE = re.compile(r"^## (R\d+)\. ", re.M)
KERNEL_RE = re.compile(r"^- (K\d+) ", re.M)
REQUIRED_FIELDS = ("- Signal:", "- Action:", "- Why:", "- evidence:")
BACKTICKED = re.compile(r"`([^`]+)`")

# SKILL.md's `## ` headings, in order. `scripts/check_skill_bundles.py` reads
# this tuple out of these bytes (parsed, never imported) and compares it to the
# document's own headings, so a clause deleted from SKILL.md reds against a
# file the deletion never touched.
SKILL_MD_CLAUSES = (
    "The catalogue - pinned bytes, front-loaded as the whole job",
    "The stations - where a pass is allowed to look",
    "The residual-sensor register",
    "Clause form",
    "R1. The catalogue is bytes at a commit, never rules improvised into a prompt",
    "R2. A catalogue hit is a hypothesis until its recipe runs",
    "R3. Reader-only against the subject; experiments run in throwaway clones",
    "R4. A finding is a record with an experiment block, not prose with a number",
    "R5. Escalation is one signal to the dispatcher, from a bounded list of classes",
    "R6. The catalogue grows only by adjudicated verdict and shrinks only by a landed gate",
    "R7. The instrument reports its own failure to bend the curve",
    "R8. A resident station runs at the closed boundary and leaves a record",
    "R9. Every gap the gates cannot close carries a sensor and a trigger",
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

# No module in this bundle may spawn a process or open a socket. This is the
# reader property one level UNDER the verb patterns: a module that cannot run a
# command or reach the network cannot file, whatever strings it happens to
# hold. It is also the only form of the check that can cover the scanner
# itself, which necessarily carries the verbs it looks for (its pattern table
# and its own planted control), and is why the verb scan exempts exactly that
# one file by name instead of leaving a script unchecked.
NO_REACH_IMPORTS = {"subprocess", "urllib", "requests", "http", "socket", "ftplib", "os"}
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.M)
VERB_SCAN_EXEMPT = "validate_red_team.py"

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

# --------------------------------------------------------------------------
# the stations, the register, and the arrival row the station is tracked in
#
# `domain/observation-topology.json` is the vocabulary for BOTH the target rows
# and the run ledger's `subject` field. One declaration, two readers: a second
# list of station names in the ledger is the copy that would drift.
TARGET_FIELDS = ("station", "inputs", "access", "feedback")
RUNBOOK_FIELDS = ("path", "step", "receipt")

REGISTER_FIELDS = ("gap", "no_mechanical_form", "sensor", "escalation")
REGISTER_STATUSES = ("OPEN", "SENSOR_FIRED_ESCALATION_LANDED", "GATED")
SENSOR_FIELDS = ("readback", "phrase", "how")
ESCALATION_FIELDS = ("trigger", "path")
PROVIDER_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$")

# The reflexive rule's marker. A ceiling admitted anywhere in this bundle names
# the register row that watches it, on the same line, or it is an exemption
# wearing prose. The scan skips exactly the file that owns it, for the same
# reason `VERB_SCAN_EXEMPT` does: the scanner necessarily carries the phrase it
# looks for, and the row it points at is where that limit is registered.
CEILING_MARKER = re.compile(r"(?i)structural ceiling")  # CEILING:reflexive-marker-discipline
CEILING_ROW = re.compile(r"CEILING:([a-z0-9-]+)")
CEILING_SCAN_GLOBS = ("*.md", "references/*.md", "domain/*.md", "domain/*.json", "scripts/*.py")

# The arrival ledger is another bundle's file and stays that way: this reads the
# row it points at and never writes one, and never restates the arrival levels
# `skills/arrival-engineering` owns.
ARRIVAL_TOPOLOGY = "skills/arrival-engineering/domain/capability-topology.json"
# A record whose boundary ends here was produced against a fixture, so it is
# sandbox arrival and nothing more. Anything else is a real generation.
FIXTURE_BOUNDARY = "-fixture"

# The set is this bundle's own, not a copy of the repository's skill list: a
# name belongs here when red-team's page must state a differential against it,
# which is a per-bundle judgement and the reason `registry.json` cannot supply
# it. `ed3c/skill-concerns#95` fixed the membership at five skills - the three
# judgment angles this pass was not, plus the two surfaces the station's own
# carriers reach into. `ed3c/skill-concerns#75` made it six: the architecture
# angle stopped being an unadmitted name and became bytes in this tree.
NEIGHBOURS = {
    "spatial-loop-grounded": "issues clause verdicts over supervised conduct",
    "context-closure-engineering": "compiles and checks one bounded context projection",
    "dynamic-workflow": "classifies runtime liveness of dispatch lanes",
    "control-noodle": "decides whether an atom's boundary was conducted correctly",
    "arrival-engineering": "audits whether a declared capability is wired to anything",
    # The architecture angle landed with ed3c/skill-concerns#75. It sat in
    # `ABSENT_NEIGHBOUR` while its bytes were unavailable, with an arm that red
    # the moment the absence ended -- an exit with no expiry is the free-exit
    # class this bundle catalogues, aimed at itself. The exit has now expired
    # and is gone rather than left standing: this boundary term is verified
    # against bytes like the other five.
    "shadow-architect": "judges the architecture shape of a change and asks",
}


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


def check_catalogue(catalogue: dict, repo_root: Path, errors: list[str]) -> None:
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
        # A cure that covers ONE instance cannot go in `gate_ref`: that field is
        # the lifecycle switch for the whole class, and an active row naming one
        # reds two branches up. So it goes in `covered_instance` - and it is
        # RESOLVED here against the carrier's own bytes rather than described in
        # prose, the same way `check_method_claims` resolves a claim's refs.
        # Renaming the function or any of the diagnostics reds against a file
        # this row never touched; a paragraph naming them re-reads as nothing.
        covered = entry.get("covered_instance")
        if covered is None:
            continue
        if not isinstance(covered, dict):
            errors.append(f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: covered_instance is not a record")
            continue
        if not str(entry.get("status_why") or "").strip():
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: a covered instance is named and "
                "status_why does not say why the class is still sampled"
            )
        carrier_ref = str(covered.get("carrier") or "")
        carrier = repo_root / carrier_ref
        if not carrier_ref or not carrier.is_file():
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: covered_instance carrier "
                f"{carrier_ref!r} is not a file in this tree"
            )
            continue
        text = carrier.read_text(encoding="utf-8")
        symbol = str(covered.get("symbol") or "")
        # `def {symbol}(`, not `def {symbol}`: the open paren is what makes a
        # rename red. Without it `scan_host_observation` still matches
        # `scan_host_observation_renamed` and the tie passes over the rename it
        # exists to catch - measured, not reasoned about.
        if not symbol or f"def {symbol}(" not in text:
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: covered_instance names "
                f"{symbol!r}, which {carrier_ref} does not define"
            )
        diagnostics = covered.get("diagnostics")
        if not isinstance(diagnostics, list) or not diagnostics:
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: covered_instance names no "
                "diagnostic, so it records a symbol that refuses nothing"
            )
            continue
        for diagnostic in diagnostics:
            if str(diagnostic) not in text:
                errors.append(
                    f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}: covered_instance names "
                    f"{diagnostic!r}, which {carrier_ref} cannot emit"
                )


def check_observation_topology(skill_root: Path, errors: list[str]) -> dict[str, Any]:
    """The stations: what a pass may read, and where its feedback may go.

    Returns `{target id: arrival row it is tracked in}`. The keys are the run
    ledger's `subject` vocabulary. A station is a row like any other here -
    inputs enumerated,
    access mode declared, feedback path declared - so the generation-close
    station is checked by the same bytes that check the wave one instead of by
    an author remembering it is different.
    """
    path = skill_root / "domain" / "observation-topology.json"
    if not path.is_file():
        errors.append(
            "OBSERVATION_TARGET_UNGROUNDED:domain/observation-topology.json: absent, so "
            "nothing declares where a pass is allowed to look"
        )
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    modes = document.get("access_modes")
    feedback_paths = document.get("feedback_paths")
    targets = document.get("targets")
    if not isinstance(modes, dict) or not modes:
        errors.append("OBSERVATION_TARGET_UNGROUNDED:access_modes: not a vocabulary")
        modes = {}
    if not isinstance(feedback_paths, dict) or not feedback_paths:
        errors.append("OBSERVATION_TARGET_UNGROUNDED:feedback_paths: not a vocabulary")
        feedback_paths = {}
    if not isinstance(targets, list) or not targets:
        errors.append("OBSERVATION_TARGET_UNGROUNDED:targets: the topology carries no stations")
        return {}
    declared: dict[str, Any] = {}
    for target in targets:
        if not isinstance(target, dict):
            errors.append("OBSERVATION_TARGET_UNGROUNDED:<unidentified>: target is not a record")
            continue
        target_id = target.get("id")
        if not isinstance(target_id, str) or not target_id:
            errors.append("OBSERVATION_TARGET_UNGROUNDED:<unidentified>: target has no id")
            continue
        if target_id in declared:
            errors.append(f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: id duplicated")
        declared[target_id] = target.get("arrival_row")
        for field in TARGET_FIELDS:
            if not target.get(field):
                errors.append(f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: no {field}")
        inputs = target.get("inputs")
        if not isinstance(inputs, list) or not all(
            isinstance(item, str) and item.strip() for item in inputs or []
        ):
            errors.append(
                f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: inputs are not enumerated, so "
                "what the pass reads at this station is whatever it finds"
            )
        if target.get("access") not in modes:
            errors.append(
                f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: access {target.get('access')!r} "
                f"is outside {sorted(modes)}"
            )
        if target.get("feedback") not in feedback_paths:
            errors.append(
                f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: feedback "
                f"{target.get('feedback')!r} is outside {sorted(feedback_paths)}"
            )
        check_runbook(skill_root, target_id, target.get("runbook"), errors)
    return declared


def check_runbook(
    skill_root: Path, target_id: str, runbook: Any, errors: list[str]
) -> None:
    """A station's step exists as a document, and names its completion receipt.

    A runbook pointer that resolves to nothing is the spec-first-lifecycle class
    this bundle catalogues, aimed at its own procedure: the row would declare a
    named step in a close-out nobody can read. The receipt is checked as bytes
    too, because "the record is the completion" is only true while the ledger
    the step names is the ledger that exists.
    """
    if runbook is None:
        return
    if not isinstance(runbook, dict):
        errors.append(f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: runbook is not a record")
        return
    for field in RUNBOOK_FIELDS:
        if not str(runbook.get(field) or "").strip():
            errors.append(f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: runbook has no {field}")
            return
    document = skill_root / runbook["path"]
    if not document.is_file():
        errors.append(
            f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: runbook {runbook['path']} does not "
            "resolve, so the named close-out step is a declaration with no procedure"
        )
        return
    text = document.read_text(encoding="utf-8")
    if runbook["step"] not in text:
        errors.append(
            f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: runbook {runbook['path']} names no "
            f"step {runbook['step']!r}"
        )
    if runbook["receipt"] not in text:
        errors.append(
            f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: runbook {runbook['path']} does not "
            f"name {runbook['receipt']} as the step's completion receipt"
        )
    if not (skill_root / runbook["receipt"]).exists():
        errors.append(
            f"OBSERVATION_TARGET_UNGROUNDED:{target_id}: the completion receipt "
            f"{runbook['receipt']} does not exist"
        )


def check_register(skill_root: Path, repo_root: Path, errors: list[str]) -> set[str]:
    """Every known gap carries a sensor that would see it, and a trigger.

    Four required fields, and the two that could be prose are checked as
    references instead: the sensor names a readback this tree can open and a
    phrase that is actually in it, so a sensor pointing at a duty nobody wrote
    reds rather than reading as coverage. That is the whole difference between
    this register and a list of caveats.
    """
    path = skill_root / "domain" / "residual-sensor-register.json"
    if not path.is_file():
        errors.append(
            "CEILING_WITHOUT_SENSOR:domain/residual-sensor-register.json: absent, so no "
            "gap in this bundle has a sensor watching it"
        )
        return set()
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get("rows")
    if not isinstance(rows, list) or not rows:
        errors.append("CEILING_WITHOUT_SENSOR:rows: the register carries no rows")
        return set()
    declared: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("CEILING_WITHOUT_SENSOR:<unidentified>: row is not a record")
            continue
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id:
            errors.append("CEILING_WITHOUT_SENSOR:<unidentified>: row has no id")
            continue
        if row_id in declared:
            errors.append(f"CEILING_WITHOUT_SENSOR:{row_id}: id duplicated")
        declared.add(row_id)
        missing = [field for field in REGISTER_FIELDS if not row.get(field)]
        if missing:
            errors.append(
                f"CEILING_WITHOUT_SENSOR:{row_id}: missing {missing}; a gap without all four "
                "of gap, no_mechanical_form, sensor and escalation is a caveat, not a row"
            )
            continue
        check_sensor(repo_root, row_id, row["sensor"], errors)
        escalation = row["escalation"]
        if not isinstance(escalation, dict):
            errors.append(f"CEILING_WITHOUT_SENSOR:{row_id}: escalation is not a record")
            continue
        for field in ESCALATION_FIELDS:
            if not str(escalation.get(field) or "").strip():
                errors.append(f"CEILING_WITHOUT_SENSOR:{row_id}: escalation has no {field}")
        status = row.get("status")
        if status not in REGISTER_STATUSES:
            errors.append(
                f"CEILING_WITHOUT_SENSOR:{row_id}: status {status!r} is outside "
                f"{list(REGISTER_STATUSES)}"
            )
            continue
        landed = escalation.get("landed")
        if status == "GATED" and not str(row.get("gate_ref") or "").strip():
            errors.append(
                f"CEILING_WITHOUT_SENSOR:{row_id}: GATED with no gate to point at"
            )
        if status == "SENSOR_FIRED_ESCALATION_LANDED" and not (
            isinstance(landed, str) and PROVIDER_REF.fullmatch(landed)
        ):
            errors.append(
                f"CEILING_WITHOUT_SENSOR:{row_id}: the status says the escalation landed and "
                f"escalation.landed {landed!r} is not a provider ref that says where"
            )
        if status == "OPEN" and landed:
            errors.append(
                f"CEILING_WITHOUT_SENSOR:{row_id}: escalation.landed names {landed!r} while "
                "the row is still OPEN; a landed tightening moves the status"
            )
    return declared


def check_sensor(repo_root: Path, row_id: str, sensor: Any, errors: list[str]) -> None:
    """The sensor is a readback that exists, holding the phrase the row cites."""
    if not isinstance(sensor, dict):
        errors.append(f"CEILING_WITHOUT_SENSOR:{row_id}: sensor is not a record")
        return
    for field in SENSOR_FIELDS:
        if not str(sensor.get(field) or "").strip():
            errors.append(f"CEILING_WITHOUT_SENSOR:{row_id}: sensor has no {field}")
            return
    readback = repo_root / sensor["readback"]
    if not readback.is_file():
        errors.append(
            f"CEILING_WITHOUT_SENSOR:{row_id}: sensor readback {sensor['readback']} does not "
            "exist, so nothing is watching this gap"
        )
        return
    if sensor["phrase"] not in readback.read_text(encoding="utf-8"):
        errors.append(
            f"CEILING_WITHOUT_SENSOR:{row_id}: sensor readback {sensor['readback']} does not "
            f"carry {sensor['phrase']!r}, so the row cites a surface that moved"
        )


def check_ceiling_markers(
    skill_root: Path, register_ids: set[str], errors: list[str]
) -> None:
    """A ceiling admitted in this bundle names the row that watches it."""
    scanned = {
        path
        for pattern in CEILING_SCAN_GLOBS
        for path in skill_root.glob(pattern)
        if path.is_file() and path.name != VERB_SCAN_EXEMPT
    }
    for path in sorted(scanned):
        relative = path.relative_to(skill_root).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not CEILING_MARKER.search(line):
                continue
            named = CEILING_ROW.findall(line)
            if not named:
                errors.append(
                    f"CEILING_WITHOUT_SENSOR:{relative}:{number}: a ceiling is admitted here "
                    "and no register row is named on the line; an admitted gap with no "
                    "sensor is an exemption with better manners"
                )
                continue
            for row_id in named:
                if row_id not in register_ids:
                    errors.append(
                        f"CEILING_WITHOUT_SENSOR:{relative}:{number}: names register row "
                        f"{row_id!r}, which does not exist"
                    )


def check_station_arrival(
    repo_root: Path, targets: dict, ledger: dict | None, errors: list[str]
) -> None:
    """A station's arrival row and this bundle's own ledger say the same thing.

    Pointer, never a copy: the arrival levels and their receipt kinds belong to
    `skills/arrival-engineering`, and this only reads the row a station names.
    What it ties is the half that ledger cannot see - whether a real generation
    has produced a record here yet - so the station cannot quietly outgrow the
    row that tracks it, and the row cannot claim a run that never happened.
    """
    if ledger is None:
        return
    records = ledger.get("records") or []
    path = repo_root / ARRIVAL_TOPOLOGY
    rows: list = []
    if path.is_file():
        rows = json.loads(path.read_text(encoding="utf-8")).get("rows") or []
    for target_id, row_id in sorted(targets.items()):
        if not row_id:
            continue
        produced = [
            record
            for record in records
            if isinstance(record, dict)
            and record.get("subject") == target_id
            and not str(record.get("boundary") or "").endswith(FIXTURE_BOUNDARY)
        ]
        if not path.is_file():
            errors.append(
                f"STATION_ARRIVAL_UNTIED:{row_id}: {ARRIVAL_TOPOLOGY} is absent, so the "
                "station's arrival is tracked by nothing"
            )
            return
        row = next((item for item in rows if item.get("id") == row_id), None)
        if row is None:
            errors.append(
                f"STATION_ARRIVAL_UNTIED:{row_id}: station {target_id} names this arrival "
                f"row and {ARRIVAL_TOPOLOGY} does not carry it"
            )
            continue
        has_run = any(
            isinstance(receipt, dict) and receipt.get("kind") == "run"
            for receipt in row.get("receipts") or []
        )
        if produced and not has_run:
            errors.append(
                f"STATION_ARRIVAL_UNTIED:{row_id}: {len(produced)} record(s) for station "
                f"{target_id} came from a real boundary while the arrival row still carries "
                "no run-kind receipt; the station has outgrown the row that tracks it"
            )
        if has_run and not produced:
            errors.append(
                f"STATION_ARRIVAL_UNTIED:{row_id}: the arrival row carries a run-kind receipt "
                f"while every record for station {target_id} came from a fixture"
            )


def derived_column_errors(position: int, record: dict) -> list[str]:
    """`judge_gaps` and `duplicate_blocks` are views of the record's own `hits`.

    The producer builds one finding per hit, so `judge_gaps` IS
    `sum(hits.values())` and `duplicate_blocks` IS the `duplicate-discovery`
    entry renamed. Committed as three columns they read as three measurements,
    and the wave-21 record is the worked example: 23 and 10 were quoted as the
    wave's numbers while a hand triage had reduced them to 4
    (ed3c/skill-concerns#130). Nothing here can judge a triage - what it CAN do
    is refuse a record whose columns disagree with the hits it carries, so a
    triaged number typed into the ledger reds instead of passing as a produced
    one. Records are append-only, so the honest form of a re-reading is a new
    record, never an edit of the committed one.
    """
    hits = record.get("hits")
    if not isinstance(hits, dict) or not all(
        isinstance(count, int) for count in hits.values()
    ):
        return [f"run record {position} hits is not a table of counts"]
    derived = {
        "judge_gaps": sum(hits.values()),
        "duplicate_blocks": hits.get("duplicate-discovery", 0),
    }
    return [
        f"run record {position} {field}={record[field]!r} disagrees with its own hits, "
        f"which derive {value}; the column is a view of `hits`, never a second "
        "measurement, so a number that differs was typed rather than produced"
        for field, value in derived.items()
        if field in record and record[field] != value
    ]


def check_ledger(skill_root: Path, targets: set[str], errors: list[str]) -> dict | None:
    """Record shape, and the one append-only property a single file can carry.

    A string saying "append_only" is not a check - it is the HOST_OBSERVED exit
    this bundle catalogues as free-exit, aimed at itself. What one file state
    CAN carry is that `run_id` is the producer's derived clock: it must parse
    as an ISO-8601 instant and must not go backwards, so a hand-typed label or
    a record inserted before an existing one reds. The rest of append-only is
    carried by git history and branch protection, not by this file, and this
    docstring is where that ceiling is named rather than implied.
    """
    path = skill_root / "domain" / "run-ledger.json"
    if not path.is_file():
        errors.append("domain/run-ledger.json missing")
        return None
    ledger = json.loads(path.read_text(encoding="utf-8"))
    records = ledger.get("records")
    if not isinstance(records, list):
        errors.append("run ledger carries no records list")
        return ledger
    previous: datetime | None = None
    for position, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"run record {position} is not an object")
            continue
        for field in (
            "run_id",
            "wave",
            "boundary",
            "subject",
            "classes_sampled",
            "hits",
            "novel_class_candidates",
            "judge_gaps",
            "duplicate_blocks",
        ):
            if field not in record:
                errors.append(f"run record {position} has no {field!r}")
        if "subject" in record and record["subject"] not in targets:
            errors.append(
                f"OBSERVATION_TARGET_UNGROUNDED:run record {position}: subject "
                f"{record['subject']!r} is outside the stations "
                f"domain/observation-topology.json declares {sorted(targets)}"
            )
        errors.extend(derived_column_errors(position, record))
        try:
            stamp = datetime.fromisoformat(str(record.get("run_id")))
        except ValueError:
            errors.append(
                f"run record {position} run_id {record.get('run_id')!r} is not the "
                "producer's ISO-8601 instant; the field is derived, never typed"
            )
            continue
        if previous is not None and stamp < previous:
            errors.append(
                f"run record {position} run_id {record['run_id']!r} precedes the record "
                "before it; an append-only ledger does not go backwards"
            )
        previous = stamp
    return ledger


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


def check_method_claims(catalogue: dict, repo_root: Path, errors: list[str]) -> None:
    """A method claim is grounded the same way a cure is, or it is not evidence.

    `method_claims` are the catalogue's non-detector grounds - the operator
    adjudication that drew the injection boundary, the judgement that the
    pinned method is worth pinning. They cannot carry a falsification recipe,
    because there is no detector to run. What they CAN carry, and what an
    exemption would let them skip, is the readback every other grounded thing
    in this repository carries: WHO adjudicated it, in WHAT form, at a ref
    whose shape matches the claim. That decision already lives once, in
    `scripts/cure_authorization.py`, so it is called rather than re-spelled -
    an unauthorized method claim reds with the same diagnostic an unauthorized
    cure does.

    One tie is owned here rather than there, because it is about grounding
    rather than about the authorization's shape: the adjudication issue an
    operator ref names must also be one of the claim's own `refs`. That is what
    makes "existence-checked" true offline - `gen_red_team_receipts` projects `refs` into
    `receipts.json`, and `scripts/maintain_skills.py` re-resolves every ref it
    finds there at the provider, so an adjudication issue that stopped existing
    comes back from a sweep that already runs.
    """
    import cure_authorization  # noqa: PLC0415

    claims = catalogue.get("method_claims")
    if claims is None:
        return
    if not isinstance(claims, dict):
        errors.append("method_claims is not a table")
        return
    for claim_id, entry in sorted(claims.items()):
        if not isinstance(entry, dict):
            errors.append(f"CATALOGUE_ENTRY_UNGROUNDED:{claim_id}: not a record")
            continue
        if not str(entry.get("claim") or "").strip():
            errors.append(f"CATALOGUE_ENTRY_UNGROUNDED:{claim_id}: no claim")
        refs = entry.get("refs")
        if not refs:
            errors.append(
                f"CATALOGUE_ENTRY_UNGROUNDED:{claim_id}: no provider ref, so the cadence "
                "sweep has nothing to re-resolve"
            )
        authorization = entry.get("authorization")
        for problem in cure_authorization.authorization_errors(
            authorization, tree=repo_root
        ):
            errors.append(
                f"{cure_authorization.DIAGNOSTIC}:{claim_id}: {problem}; a method claim "
                "is evidence only once it names who adjudicated it and what artifact "
                "carries the adjudication"
            )
        issue = ((authorization or {}).get("adjudication") or {}).get("issue") if isinstance(
            authorization, dict
        ) else None
        if issue and issue not in (refs or []):
            errors.append(
                f"{cure_authorization.DIAGNOSTIC}:{claim_id}: the adjudication issue "
                f"{issue} is not among the claim's refs, so the cadence sweep never "
                "re-resolves the artifact this claim rests on"
            )


def check_recipes_parse(catalogue: dict, errors: list[str]) -> None:
    """Every recipe step that invokes the driver goes through the real parser.

    `COMMAND_RE` only certifies that a step LOOKS like a command. A recipe
    naming a flag the driver does not have satisfies that and still exits 2 the
    first time anyone runs it - a runnable-command-sequence field that
    certifies unrunnable sequences is the opinion registry the field exists to
    prevent. This runs the tokens through `shadow_driver.build_parser()`
    itself, so the recipes cannot drift from the option surface.
    """
    import shadow_driver  # noqa: PLC0415

    parser = shadow_driver.build_parser()
    for entry in catalogue.get("classes") or []:
        if not isinstance(entry, dict):
            continue
        recipe = ((entry.get("falsification") or {}).get("recipe")) or []
        for step in recipe:
            if not isinstance(step, str):
                continue
            try:
                tokens = shlex.split(step)
            except ValueError:
                errors.append(
                    f"CATALOGUE_ENTRY_UNGROUNDED:{entry.get('id')}: recipe step does not "
                    f"tokenize: {step!r}"
                )
                continue
            if len(tokens) < 2 or tokens[0] != "python3":
                continue
            if not tokens[1].endswith("shadow_driver.py"):
                continue
            _, extra = parser.parse_known_args(tokens[2:])
            unknown = [token for token in extra if token.startswith("-")]
            if unknown:
                errors.append(
                    f"CATALOGUE_ENTRY_UNGROUNDED:{entry.get('id')}: recipe names "
                    f"{unknown} which shadow_driver.build_parser() does not accept, so "
                    "the step exits 2 before the experiment runs"
                )


def check_no_reach(path: Path, errors: list[str]) -> None:
    """No module in the bundle may import a way to run a command or open a socket."""
    if not path.is_file():
        errors.append(f"DRIVER_SURFACE_FORBIDDEN:{path.name}: script absent")
        return
    for module in IMPORT_RE.findall(path.read_text(encoding="utf-8")):
        if module.split(".")[0] in NO_REACH_IMPORTS:
            errors.append(
                f"DRIVER_SURFACE_FORBIDDEN:{path.name}: imports {module!r}; nothing in "
                "this bundle may spawn a process or reach the network"
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
    from gen_red_team_receipts import ReceiptRefused, render  # noqa: PLC0415

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
            "receipts.json is not what gen_red_team_receipts.py produces from the catalogue - "
            "regenerate it with its producer; a hand-edited receipt is laundering even "
            "when the edit would be factually right"
        )


def check_roles(skill_root: Path, errors: list[str]) -> None:
    for relative in ("SKILL.md", "README.md"):
        path = skill_root / relative
        if not path.is_file():
            errors.append(f"{relative} missing")
            continue
        block = roles_block(path.read_text(encoding="utf-8"))
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

    The scan is scoped to the Non-claims section, not the whole document. Over
    the whole document any incidental mention satisfies it - a path like
    `skills/arrival-engineering/...` in a paragraph about something else is
    enough - so the check would be green for a neighbour whose differential was
    never stated, which is the grep-verifiability this section is supposed to
    carry, hollowed.
    """
    text = section_text(text, "Non-claims")
    for name in NEIGHBOURS:
        if name not in text:
            errors.append(f"Non-claims does not name the neighbour it is not: {name}")
        elif not (repo_root / "skills" / name).is_dir():
            errors.append(f"neighbour {name} named but absent from this tree")


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
    check_catalogue(catalogue, repo_root, errors)
    check_method_claims(catalogue, repo_root, errors)
    targets = check_observation_topology(skill_root, errors)
    ledger = check_ledger(skill_root, targets, errors)
    check_station_arrival(repo_root, targets, ledger, errors)
    check_ceiling_markers(skill_root, check_register(skill_root, repo_root, errors), errors)
    # Every executable in the bundle, not just the driver: the Non-claim is
    # written about the bundle, so the scan that keeps it true has to cover the
    # bundle. A scan over one of five scripts proves the property for one file
    # and gets read as proving it for all five.
    for script in sorted((skill_root / "scripts").glob("*.py")):
        check_no_reach(script, errors)
        if script.name != VERB_SCAN_EXEMPT:
            check_forbidden_surface(script, errors)
    check_recipes_parse(catalogue, errors)
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

        def rename_covered_diagnostic(copy: Path) -> None:
            edit_catalogue(
                copy,
                lambda body: body["classes"][1]["covered_instance"]["diagnostics"]
                .__setitem__(0, "RECEIPT_HOST_OBSERVED_RENAMED"),
            )

        mutate(
            "covered_instance_naming_a_diagnostic_the_carrier_cannot_emit_reds",
            rename_covered_diagnostic,
            "which scripts/check_skill_bundles.py cannot emit",
        )

        def truncate_covered_symbol(copy: Path) -> None:
            # A PREFIX of the real name, on purpose. The first cut of this tie
            # asked `f"def {symbol}" in text`, which a prefix satisfies, so the
            # arm the tie exists for - a rename - passed. The carrier-side
            # control caught it; this arm is that control, committed.
            edit_catalogue(
                copy,
                lambda body: body["classes"][1]["covered_instance"].__setitem__(
                    "symbol", "scan_host_observ"
                ),
            )

        mutate(
            "covered_instance_naming_a_prefix_of_a_real_definition_reds",
            truncate_covered_symbol,
            "which scripts/check_skill_bundles.py does not define",
        )

        def silent_covered_instance(copy: Path) -> None:
            edit_catalogue(
                copy, lambda body: body["classes"][1].__setitem__("status_why", "")
            )

        mutate(
            "covered_instance_without_a_status_argument_reds",
            silent_covered_instance,
            "status_why does not say why the class is still sampled",
        )

        def edit_json(copy: Path, relative: str, change) -> None:
            path = copy / relative
            body = json.loads(path.read_text(encoding="utf-8"))
            change(body)
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        def undeclared_station(copy: Path) -> None:
            edit_json(
                copy,
                "domain/run-ledger.json",
                lambda body: body["records"][0].__setitem__("subject", "some-other-seam"),
            )

        mutate(
            "run_record_naming_an_undeclared_station_reds",
            undeclared_station,
            "OBSERVATION_TARGET_UNGROUNDED:run record 0",
        )

        def unpointed_runbook(copy: Path) -> None:
            def change(body):
                for target in body["targets"]:
                    if target.get("runbook"):
                        target["runbook"]["path"] = "domain/a-runbook-nobody-wrote.md"

            edit_json(copy, "domain/observation-topology.json", change)

        mutate(
            "runbook_pointer_that_resolves_to_nothing_reds",
            unpointed_runbook,
            "does not resolve, so the named close-out step",
        )

        def register_row_missing_a_field(copy: Path) -> None:
            edit_json(
                copy,
                "domain/residual-sensor-register.json",
                lambda body: body["rows"][0].pop("sensor"),
            )

        mutate(
            "register_row_without_all_four_fields_reds",
            register_row_missing_a_field,
            "CEILING_WITHOUT_SENSOR:rubber-stamp-authorization: missing",
        )

        def sensor_pointing_nowhere(copy: Path) -> None:
            edit_json(
                copy,
                "domain/residual-sensor-register.json",
                lambda body: body["rows"][1]["sensor"].__setitem__(
                    "readback", "skills/red-team/domain/a-readback-nobody-wrote.json"
                ),
            )

        mutate(
            "sensor_readback_that_does_not_exist_reds",
            sensor_pointing_nowhere,
            "does not exist, so nothing is watching this gap",
        )

        def prose_ceiling_with_no_row(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nThis pass samples by judgement, which is a structural ceiling.\n",
                encoding="utf-8",
            )

        mutate(
            "prose_ceiling_without_a_register_row_reds",
            prose_ceiling_with_no_row,
            "a ceiling is admitted here and no register row is named",
        )

        def station_outgrew_its_row(copy: Path) -> None:
            def change(body):
                # The subject to plant against is chosen by IDENTITY, never by
                # position. `records[-1]` is whichever station ran last in an
                # append-only ledger, so the first record appended for a station
                # with no arrival row turned this arm into a silent no-op:
                # `check_station_arrival` skips untracked stations, so the
                # planted record reported nothing and the control still passed.
                topology = json.loads(
                    (copy / "domain" / "observation-topology.json").read_text(
                        encoding="utf-8"
                    )
                )
                tracked = {
                    row.get("id")
                    for row in topology.get("targets") or []
                    if row.get("arrival_row")
                }
                record = dict(
                    next(
                        item
                        for item in body["records"]
                        if item.get("subject") in tracked
                    )
                )
                record["run_id"] = "2026-12-01T00:00:00+00:00"
                record["boundary"] = "generation-close"
                body["records"].append(record)

            edit_json(copy, "domain/run-ledger.json", change)

        mutate(
            "station_that_outgrew_its_arrival_row_reds",
            station_outgrew_its_row,
            "STATION_ARRIVAL_UNTIED",
        )

        def garbage_operator_ref(copy: Path) -> None:
            import cure_authorization  # noqa: PLC0415

            def change(body):
                for claim in body["method_claims"].values():
                    claim["authorization"] = {
                        "kind": "operator-adjudication",
                        "ref": cure_authorization.VIBES_REF,
                    }

            edit_catalogue(copy, change)

        mutate(
            "method_claim_with_a_well_formed_ref_resolving_to_nothing_reds",
            garbage_operator_ref,
            "names no adjudication artifact",
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

        mutate("hand_edited_receipts_red", hand_edit_receipts, "not what gen_red_team_receipts.py produces")

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

        def name_a_neighbour_outside_non_claims(copy: Path) -> None:
            """Delete only the bullet; `skills/arrival-engineering` stays elsewhere.

            The document still contains the string, so a whole-document scan
            stays green here while the differential it was supposed to make
            grep-verifiable is gone. This is the mutation that separates the
            scoped check from the hollow one.
            """
            path = copy / "SKILL.md"
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            kept = [line for line in lines if not line.startswith("- No ceremony and no wiring audit.")]
            assert len(kept) == len(lines) - 1, "the bullet this mutation removes moved"
            path.write_text("".join(kept), encoding="utf-8")
            assert "arrival-engineering" in path.read_text(encoding="utf-8")

        mutate(
            "neighbour_named_only_outside_non_claims_reds",
            name_a_neighbour_outside_non_claims,
            "does not name the neighbour it is not: arrival-engineering",
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
