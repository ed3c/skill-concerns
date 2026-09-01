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
from audit_islands import DIAGNOSTICS, LEVELS, SURFACES, supported_arrival  # noqa: E402
from gen_receipts import render  # noqa: E402

CLAUSE_RE = re.compile(r"^## (A\d+)\. ", re.M)
KERNEL_RE = re.compile(r"^- (K\d+) ", re.M)
REQUIRED_FIELDS = ("- Signal:", "- Action:", "- Why:", "- evidence:")
BACKTICKED = re.compile(r"`([^`]+)`")
LAW_RE = re.compile(r"\bLAW-[A-Z-]+\b")
ROLE_TOKENS = ("BUILD", "SHADOW", "reader-only", "S0", "S1", "S2")
CLOSURE_OWNER = "../context-closure-engineering/references/portable-context-closure-policy.md"
POINTED_LAWS = {"LAW-TRACE-GAP", "LAW-NO-PROMOTION"}
# The other two axes that also count from L0. Naming them is what stops an
# arrival level being read as an admitted evidence ceiling.
OTHER_L_AXES = ("L0 procedural", "L0_SOURCE_FREEZE")
RUN_SHAPED = ("chore.txt", "calls.log", "terminal-state.txt", "actor-final-message.txt")


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
    """This bundle owns L0/L1/L2 arrival, and must not be confusable with the
    two other axes in this repository that also count from L0."""
    for level in LEVELS:
        if f"**{level} " not in text:
            errors.append(f"arrival level {level} is not defined in SKILL.md")
    for axis in OTHER_L_AXES:
        if axis not in text:
            errors.append(
                f"SKILL.md does not disambiguate arrival levels from the {axis!r} axis - "
                "three numberings starting at L0 on one page is how a sandbox arrival "
                "gets read as an admitted evidence ceiling"
            )
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
        claimed = row.get("arrival")
        if claimed not in LEVELS:
            errors.append(f"topology row {row_id!r} arrival {claimed!r} is not one of {LEVELS}")
        elif LEVELS.index(claimed) > LEVELS.index(supported):
            errors.append(
                f"CLAIM_ABOVE_ARRIVAL:{row_id}: records {claimed} while its receipts "
                f"support only {supported}"
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
                    row["arrival"] = "L2"
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate("claim_above_arrival_reds", overclaim, "CLAIM_ABOVE_ARRIVAL")

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

        def drop_disambiguation(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("L0_SOURCE_FREEZE", "the ceiling"),
                encoding="utf-8",
            )

        mutate("undisambiguated_l_numbering_reds", drop_disambiguation, "does not disambiguate")
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
