#!/usr/bin/env python3
"""Deterministic validator for the arrival-engineering bundle.

Every check here is a TIE between two places that must agree, so a hollowed
document goes red instead of quietly describing a mechanism that no longer
exists:

  clauses  <-> kernel entries        (count-tied, one kernel per clause)
  clauses  <-> receipts evidence ids (every clause cited, every entry bound)
  A1 prose <-> audit_islands.SURFACES (the five surfaces, by name, both ways)
  Diagnostics prose <-> audit_islands.DIAGNOSTICS (by name, both ways)
  receipts.json <-> gen_receipts.render(topology) (byte-identical; hand edits red)
  topology arrival <-> the receipts that support it (no claim above arrival)

The single-declaration rule is why this file IMPORTS the surface and diagnostic
tables rather than re-listing them: a second literal is how the two sides drift.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_islands import (  # noqa: E402
    DIAGNOSTICS,
    LEVELS,
    SURFACES,
    arrival_mismatch,
    supported_arrival,
)
from gen_receipts import render  # noqa: E402

CLAUSE_RE = re.compile(r"^## (A\d+)\. ", re.M)
KERNEL_RE = re.compile(r"^- (K\d+) ", re.M)
REQUIRED_FIELDS = ("- Signal:", "- Action:", "- Why:", "- evidence:")
BACKTICKED = re.compile(r"`([^`]+)`")
LAW_RE = re.compile(r"\bLAW-[A-Z-]+\b")
ROLE_TOKENS = ("BUILD", "SHADOW", "reader-only", "S0", "S1", "S2")
CLOSURE_OWNER = "../context-closure-engineering/references/portable-context-closure-policy.md"
POINTED_LAWS = {"LAW-TRACE-GAP", "LAW-NO-PROMOTION"}
RUN_SHAPED = ("chore.txt", "calls.log", "terminal-state.txt", "actor-final-message.txt")
# The numbering this axis used to carry. Scoped to topology row notes: SKILL.md
# and README.md name it deliberately, explaining why it is gone.
RETIRED_LEVEL_RE = re.compile(r"\bL[0-9]\b")

# SKILL.md's `## ` headings, in order. Read out of these bytes by
# `scripts/check_skill_bundles.py` (parsed, never imported) and compared to the
# document's own headings, so a clause deleted from SKILL.md reds against a
# file the deletion never touched.
SKILL_MD_CLAUSES = (
    "The arrival ledger - DECLARED / EXERCISED / PRODUCTION",
    "Clause form",
    "A1. Audit five surfaces, or the audit itself only proves declaration",
    "A2. Availability is not use: an unbound verb is a planned island",
    "A3. A claim above its measured arrival is a finding",
    'A4. Every "recorded in X" is checked against X\'s bytes',
    "A5. Cross-repo pointers are re-verified against live trees",
    "A6. Closure is by pointer to its owner, never by restatement",
    "Diagnostics",
    "Knowledge placement",
    "Non-claims",
)


def clause_bodies(text: str) -> dict[str, str]:
    sections = CLAUSE_RE.split(text)
    return {
        sections[index]: sections[index + 1].split("\n## ", 1)[0]
        for index in range(1, len(sections), 2)
    }


def section(text: str, heading: str) -> str:
    marker = f"\n## {heading}\n"
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def check_clauses(text: str, errors: list[str]) -> dict[str, str]:
    bodies = clause_bodies(text)
    if not bodies:
        errors.append("SKILL.md declares no A-clauses")
    if len(bodies) != len(set(bodies)):
        errors.append("duplicate clause ids")
    for clause_id, body in bodies.items():
        for field in REQUIRED_FIELDS:
            if field not in body:
                errors.append(f"{clause_id}: trigger form incomplete, missing {field!r}")
    return bodies


def check_kernel(skill_root: Path, bodies: dict[str, str], errors: list[str]) -> None:
    kernel_path = skill_root / "references" / "portable-arrival-kernel.md"
    if not kernel_path.is_file():
        errors.append("L0 kernel references/portable-arrival-kernel.md missing")
        return
    kernel_text = kernel_path.read_text(encoding="utf-8")
    if "L0 procedural" not in kernel_text:
        errors.append("L0 kernel does not declare itself the procedural layer")
    kernels = KERNEL_RE.findall(kernel_text)
    if len(kernels) != len(bodies):
        errors.append(
            f"kernel/clause count mismatch: {len(kernels)} kernels vs {len(bodies)} clauses"
        )
    if len(kernels) != len(set(kernels)):
        errors.append("duplicate kernel ids")


def check_evidence(bodies: dict[str, str], receipts: dict, errors: list[str]) -> None:
    evidence = receipts.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        errors.append("receipts.json evidence table missing or empty")
        return
    for key, entry in sorted(evidence.items()):
        refs = entry.get("refs") if isinstance(entry, dict) else None
        if not isinstance(refs, list) or not refs:
            errors.append(f"receipts.json evidence {key!r} has no refs")
        if not isinstance(entry, dict) or not str(entry.get("claim") or "").strip():
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


def check_surface_tie(bodies: dict[str, str], errors: list[str]) -> None:
    """A1's prose and the driver's table name the same five surfaces, both ways."""
    body = bodies.get("A1", "")
    documented = {
        token for token in BACKTICKED.findall(body) if re.fullmatch(r"[a-z][a-z_]*", token)
    }
    for missing in sorted(set(SURFACES) - documented):
        errors.append(f"A1 does not document the surface the driver scans: {missing}")
    for extra in sorted(documented - set(SURFACES)):
        errors.append(f"A1 documents a surface the driver does not scan: {extra}")


def check_diagnostic_tie(text: str, errors: list[str]) -> None:
    body = section(text, "Diagnostics")
    if not body:
        errors.append("SKILL.md has no Diagnostics section")
        return
    documented = {
        token for token in BACKTICKED.findall(body) if re.fullmatch(r"[A-Z][A-Z_]+", token)
    }
    for missing in sorted(set(DIAGNOSTICS) - documented):
        errors.append(f"Diagnostics section omits a diagnostic the driver emits: {missing}")
    for extra in sorted(documented - set(DIAGNOSTICS)):
        errors.append(f"Diagnostics section names a diagnostic the driver cannot emit: {extra}")


def check_arrival_vocabulary(text: str, topology: dict, errors: list[str]) -> None:
    """This bundle owns the arrival vocabulary, and defines every level it uses.

    There is no clause here requiring SKILL.md to disambiguate itself from the
    other two L-axes in this repository. There used to be, when this axis was
    also numbered from L0; renaming the axis - the newest of the three, and the
    only one with no consumers - removed the collision the prose was there to
    manage, and the gate that read that prose went with it.
    """
    for level in LEVELS:
        if f"**{level}**" not in text:
            errors.append(f"arrival level {level} is not defined in SKILL.md")
    declared = topology.get("arrival_levels")
    if not isinstance(declared, dict) or set(declared) != set(LEVELS):
        errors.append(f"topology arrival_levels must declare exactly {LEVELS}")


def check_closure_pointer(bodies: dict[str, str], text: str, errors: list[str]) -> None:
    body = bodies.get("A6", "")
    if CLOSURE_OWNER not in body:
        errors.append("A6 does not point at the closure law's owner file")
    named = set(LAW_RE.findall(text))
    if named != POINTED_LAWS:
        errors.append(
            f"A6 must name exactly {sorted(POINTED_LAWS)} and no other law ids; found {sorted(named)}"
        )
    if "## LAW-" in text:
        errors.append("SKILL.md restates a law section header - point at the owner, never copy it")


def check_roles(skill_root: Path, errors: list[str]) -> None:
    for relative in ("SKILL.md", "README.md"):
        path = skill_root / relative
        if not path.is_file():
            errors.append(f"{relative} missing")
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
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


def check_topology(topology: dict, repo_root: Path, errors: list[str]) -> None:
    rows = topology.get("rows")
    if not isinstance(rows, list) or not rows:
        errors.append("topology carries no rows")
        return
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("topology row is not an object")
            continue
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id:
            errors.append("topology row has no id")
            continue
        if row_id in seen:
            errors.append(f"topology row id duplicated: {row_id}")
        seen.add(row_id)
        for key in ("capability", "carrier", "arrival", "evidence"):
            if not str(row.get(key) or "").strip():
                errors.append(f"topology row {row_id!r} has no {key}")
        supported = supported_arrival(row, repo_root)
        if supported is None:
            errors.append(
                f"TOPOLOGY_ROW_WITHOUT_RECEIPT:{row_id}: no receipt resolves, so no "
                "arrival level is supported - the append refusal exists to keep this "
                "shape out of the ledger"
            )
            continue
        mismatch = arrival_mismatch(row, supported)
        if mismatch is not None:
            diagnostic, detail, _ = mismatch
            errors.append(f"{diagnostic}:{row_id}: {detail}")
        # A row's prose must speak the vocabulary the row's own column speaks.
        # Renaming the axis moved every `arrival` value mechanically and left
        # three notes still reasoning in `L1, not L2` -- true sentences about a
        # numbering this bundle had just stopped owning, which is the A4 shape
        # (a documented claim whose subject no longer carries it) inside the
        # ledger that names A4. Numbers are cheap to grep; memory is not.
        stale = RETIRED_LEVEL_RE.findall(str(row.get("note") or ""))
        if stale:
            errors.append(
                f"topology row {row_id!r} note still names the retired numbering "
                f"{sorted(set(stale))} - arrival levels are {LEVELS}"
            )


def check_receipts_are_produced(skill_root: Path, topology: dict, errors: list[str]) -> None:
    path = skill_root / "receipts.json"
    if not path.is_file():
        errors.append("receipts.json missing")
        return
    if path.read_text(encoding="utf-8") != render(topology):
        errors.append(
            "receipts.json is not what gen_receipts.py produces from the topology - "
            "regenerate it with its producer; a hand-edited receipt is laundering "
            "even when the edit would be factually right"
        )


def check_campaign(skill_root: Path, bodies: dict[str, str], errors: list[str]) -> None:
    spec_path = skill_root / "evals" / "behavioral-campaigns" / "spec.json"
    if not spec_path.is_file():
        errors.append("behavioral campaign evals/behavioral-campaigns/spec.json missing")
        return
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    status = spec.get("status")
    if status not in {"UNJUDGED", "JUDGED"}:
        errors.append(f"campaign status {status!r} is neither UNJUDGED nor JUDGED")
    if status == "JUDGED" and not (
        skill_root / "evals" / "behavioral-campaigns" / "ledger.json"
    ).is_file():
        errors.append("campaign claims JUDGED with no ledger.json recording the judged wave")

    arms = spec.get("arms")
    if not isinstance(arms, list) or len(arms) < 2:
        errors.append("campaign needs at least two arms to discriminate anything")
        arms = arms if isinstance(arms, list) else []
    giveaways = spec.get("giveaway_tokens")
    if not isinstance(giveaways, list) or not giveaways:
        errors.append("campaign declares no giveaway tokens, so the blind scan checks nothing")
        giveaways = []

    negatives = [arm for arm in arms if isinstance(arm, dict) and arm.get("control") == "negative"]
    if not negatives:
        errors.append(
            "campaign carries no control:negative arm - a judge that has never refused "
            "anything is a single arrival, not a physical standard"
        )

    for arm in arms:
        if not isinstance(arm, dict):
            errors.append("campaign arm is not an object")
            continue
        arm_id = arm.get("id")
        judge_input = arm.get("judge_input")
        if not isinstance(judge_input, str) or not (skill_root / judge_input).is_dir():
            errors.append(f"arm {arm_id!r} judge input missing: {judge_input!r}")
            continue
        root = skill_root / judge_input
        for relative in RUN_SHAPED:
            if not (root / relative).is_file():
                errors.append(f"arm {arm_id!r} is not run-shaped: {relative} missing")
        if not (root / "workspace").is_dir():
            errors.append(f"arm {arm_id!r} is not run-shaped: workspace/ missing")
        if not arm.get("criteria"):
            errors.append(
                f"arm {arm_id!r} declares no criteria - it would arrive in the batch as "
                "the one run the rubric has no entry for, which is itself a tell"
            )
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for token in giveaways:
                if token in text:
                    errors.append(
                        f"arm {arm_id!r} announces itself: giveaway {token!r} in "
                        f"{path.relative_to(skill_root).as_posix()} - it cannot measure a "
                        "refusal the judge could not have known to make"
                    )

    for arm in negatives:
        arm_id = arm.get("id")
        if arm.get("expected_verdict") != "violated":
            errors.append(f"negative arm {arm_id!r} does not declare expected_verdict 'violated'")
        answer_key = arm.get("answer_key")
        if not isinstance(answer_key, str) or not (skill_root / answer_key).is_file():
            errors.append(f"negative arm {arm_id!r} answer key missing: {answer_key!r}")
        elif isinstance(arm.get("judge_input"), str) and (
            (skill_root / answer_key).resolve().is_relative_to(
                (skill_root / arm["judge_input"]).resolve()
            )
        ):
            errors.append(f"negative arm {arm_id!r} answer key sits inside the judge input")
        clauses = arm.get("clauses")
        if not isinstance(clauses, list) or not clauses:
            errors.append(f"negative arm {arm_id!r} names no violated clauses")
        else:
            for clause in clauses:
                if clause not in bodies:
                    errors.append(
                        f"negative arm {arm_id!r} names clause {clause!r} absent from SKILL.md"
                    )


def validate(skill_root: Path, repo_root: Path | None = None) -> list[str]:
    repo_root = repo_root or skill_root.parents[1]
    errors: list[str] = []
    skill_md = skill_root / "SKILL.md"
    topology_path = skill_root / "domain" / "capability-topology.json"
    if not skill_md.is_file():
        return ["SKILL.md missing"]
    if not topology_path.is_file():
        return ["domain/capability-topology.json missing"]
    text = skill_md.read_text(encoding="utf-8")
    topology = json.loads(topology_path.read_text(encoding="utf-8"))

    bodies = check_clauses(text, errors)
    check_kernel(skill_root, bodies, errors)
    check_surface_tie(bodies, errors)
    check_diagnostic_tie(text, errors)
    check_arrival_vocabulary(text, topology, errors)
    check_closure_pointer(bodies, text, errors)
    check_roles(skill_root, errors)
    check_topology(topology, repo_root, errors)
    check_receipts_are_produced(skill_root, topology, errors)
    if "Non-claims" not in text:
        errors.append("Non-claims section missing")

    receipts_path = skill_root / "receipts.json"
    if receipts_path.is_file():
        check_evidence(bodies, json.loads(receipts_path.read_text(encoding="utf-8")), errors)
    check_campaign(skill_root, bodies, errors)
    return errors


# --------------------------------------------------------------------------
# selftest: every tie must go red when the side it ties to is hollowed


def selftest() -> int:
    real = Path(__file__).resolve().parents[1]
    repo_root = real.parents[1]
    checks: list[tuple[str, bool, str]] = []
    scratch = Path(tempfile.mkdtemp(prefix="arrival-validate-selftest-"))

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

    try:
        record(
            "positive_control_unmutated_copy_passes",
            not validate(fresh(), repo_root),
            f"errors={validate(fresh(), repo_root)[:3]}",
        )

        def drop_kernel(copy: Path) -> None:
            path = copy / "references" / "portable-arrival-kernel.md"
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            path.write_text(
                "".join(line for line in lines if not line.startswith("- K6 ")), encoding="utf-8"
            )

        mutate("dropped_kernel_entry_breaks_the_count_tie", drop_kernel, "count mismatch")

        def drop_diagnostic(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "- `POINTER_DANGLING` - a cross-repo or cross-tree pointer that does not resolve (A5).\n",
                    "",
                ),
                encoding="utf-8",
            )

        mutate(
            "undocumented_diagnostic_reds",
            drop_diagnostic,
            "Diagnostics section omits a diagnostic",
        )

        def drop_surface(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("`cli_text` (a documented", "(a documented"),
                encoding="utf-8",
            )

        mutate("undocumented_surface_reds", drop_surface, "does not document the surface")

        def hand_edit_receipts(copy: Path) -> None:
            path = copy / "receipts.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            body["evidence"]["arrival-ledger"]["refs"].append("ed3c/skill-concerns#1")
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate("hand_edited_receipts_red", hand_edit_receipts, "not what gen_receipts.py produces")

        def overclaim(copy: Path) -> None:
            path = copy / "domain" / "capability-topology.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            for row in body["rows"]:
                if row["id"] == "noodles-scip-validation-core":
                    row["arrival"] = "PRODUCTION"
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate("claim_above_arrival_reds", overclaim, "CLAIM_ABOVE_ARRIVAL")

        def underclaim(copy: Path) -> None:
            path = copy / "domain" / "capability-topology.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            for row in body["rows"]:
                if row["id"] == "sc-control-backup-checks":
                    row["arrival"] = "DECLARED"
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate("claim_below_arrival_reds", underclaim, "CLAIM_BELOW_ARRIVAL")

        def stale_numbering_in_a_note(copy: Path) -> None:
            path = copy / "domain" / "capability-topology.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            body["rows"][0]["note"] = "L1, not L2, and the difference is byte-derived."
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate(
            "retired_numbering_in_a_row_note_reds",
            stale_numbering_in_a_note,
            "still names the retired numbering",
        )

        def strip_receipts(copy: Path) -> None:
            path = copy / "domain" / "capability-topology.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            for row in body["rows"]:
                if row["id"] == "noodles-where-is-x-slice":
                    row["receipts"] = []
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate("receiptless_row_reds", strip_receipts, "TOPOLOGY_ROW_WITHOUT_RECEIPT")

        def unpoint_a6(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(CLOSURE_OWNER, "somewhere.md"),
                encoding="utf-8",
            )

        mutate("a6_without_its_owner_pointer_reds", unpoint_a6, "does not point at the closure law")

        def restate_a_law(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\n## LAW-DENOMINATOR\n\nA restated copy.\n",
                encoding="utf-8",
            )

        mutate("restated_law_section_reds", restate_a_law, "restates a law section header")

        def blow_the_blind(copy: Path) -> None:
            path = copy / "evals" / "behavioral-campaigns" / "judge-inputs" / "r-c3" / "chore.txt"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nThis is the negative control.\n",
                encoding="utf-8",
            )

        mutate("self_announcing_negative_arm_reds", blow_the_blind, "announces itself")

        def unblind_the_key(copy: Path) -> None:
            source = copy / "evals" / "behavioral-campaigns" / "fixtures" / "negative-control" / "ANSWER-KEY.md"
            target = copy / "evals" / "behavioral-campaigns" / "judge-inputs" / "r-c3" / "ANSWER-KEY.md"
            shutil.move(str(source), str(target))
            spec = copy / "evals" / "behavioral-campaigns" / "spec.json"
            body = json.loads(spec.read_text(encoding="utf-8"))
            for arm in body["arms"]:
                if arm.get("control") == "negative":
                    arm["answer_key"] = "evals/behavioral-campaigns/judge-inputs/r-c3/ANSWER-KEY.md"
            spec.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate("answer_key_inside_the_judge_input_reds", unblind_the_key, "sits inside the judge input")

        def drop_a_level_definition(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("**EXERCISED**", "EXERCISED"),
                encoding="utf-8",
            )

        mutate(
            "undefined_arrival_level_reds",
            drop_a_level_definition,
            "arrival level EXERCISED is not defined",
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
    print("PASS: arrival-engineering clause, kernel, surface, diagnostic and receipt ties intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
