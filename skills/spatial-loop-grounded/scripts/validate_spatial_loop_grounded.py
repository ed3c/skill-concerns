#!/usr/bin/env python3
"""Deterministic validator for the spatial-loop-grounded skill.

Fails closed when any clause loses its trigger form or its receipt binding:
this is the hillclimb gate - edits may add evidence and clauses, never
silently weaken them.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ab_campaign import blind_scan, terminal_state_text  # noqa: E402

CLAUSE_RE = re.compile(r"^## (C\d+)\. ", re.M)
REQUIRED_FIELDS = ("- Signal:", "- Action:", "- Why:", "- evidence:")
REF_RE = re.compile(r"^ed3c/[a-z-]+#\d+$")
# host-environment receipts (non-repository evidence) name their exact host artifact
HOST_REF_RE = re.compile(r"^host:\S+$")
KERNEL_RE = re.compile(r"^- (K\d+) ", re.M)
# cross-wave judge ledger: one entry per judged campaign
LEDGER_ENTRY_KEYS = (
    "date",
    "wave",
    "judge_model",
    "per_clause_summary",
    "negative_control_verdict",
    "gaps",
    "prompt_improvements",
    "receipt_refs",
)
GENESIS = "0" * 64

# The interpretation-time obligations a wave's interpreter must physically
# encounter. `evals/behavioral.json` has named a `protocol` path since the
# pilot, and nothing resolved it: the wave-14 lane filed a finding into that
# path while no such file existed - a NO-HOME wearing a path. Every campaign
# spec now names it too, because the spec is what an interpreter holds, and
# these anchors are read out of the resolved document, so a caveat deleted from
# the protocol reds here (ed3c/skill-concerns#79).
PROTOCOL_ANCHORS = (
    "caveat: typo-fragile-allow-list-scoring",
    "caveat: wave-1-shaped-criteria-template-bias",
)

# --- clause fixtures --------------------------------------------------------
# A clause whose only evidence is its own prose has never been evaluated. The
# behavioral campaigns need a live judge and stay outside hermetic run_all;
# these fixtures are the hermetic half. Each one is an artifact the clause is
# ABOUT, and its verdict is computed from its own bytes below - so an amendment
# that reads well and decides nothing fails closed here.
CLAUSE_FIXTURES = "evals/clause-fixtures"
HEX64_RE = re.compile(r"[0-9a-f]{64}")
# The shape every refusal in this repository prints, e.g.
# ADMISSION_STAMP_REFUSED:dynamic-workflow:NO_DECLARED_CHECKS. Quoting the gate's
# own string is what makes the escalation checkable by its owner; a paraphrase
# is a report about a refusal rather than the refusal.
REFUSAL_RE = re.compile(r"[A-Z][A-Z0-9_]*:[a-z0-9][a-z0-9-]*:[A-Z][A-Z0-9_]*")

# Count tie to this Skill's own entrypoint (ed3c/skill-concerns#74): the exact
# `## ` section headings of SKILL.md. `CLAUSE_RE` above ties the C-numbered
# clauses only; the framing sections around them -- clause form, the layer/role
# split, the non-claims -- were untied, and dropping one of those is exactly how
# a skill loses its boundaries while every clause still parses.
# `scripts/check_skill_bundles.py` reads this tuple out of these bytes, parsed
# and never imported.
SKILL_MD_CLAUSES = (
    "Clause form",
    "Concern layers and roles",
    "C1. Monitor is a reader, never a writer",
    "C2. Count decompression layers before any claim",
    "C3. FIRST_GREEN is a review point, not a completion",
    "C4. Repeated failure escalates to a quarantine packet",
    "C5. Evidence regenerates through its producer, never by hand",
    "C6. Teardown mirrors construction, gated on terminal readback",
    "C7. Newly reachable invalid states are first-class deltas",
    "C8. Bind every action to its exact subject",
    "C9. An oldest-first queue starves behind a permanently failing head",
    "C10. No completion notification means still running",
    "C11. Exit-code residue is not current state",
    "C12. An observer's silence is evidence only after it has demonstrated both directions",
    "Non-claims",
)


def entry_digest(entry: dict) -> str:
    """Chain digest of one ledger entry, prev_sha256 included."""
    canonical = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ref_ok(ref: object) -> bool:
    return isinstance(ref, str) and bool(REF_RE.fullmatch(ref) or HOST_REF_RE.fullmatch(ref))


def validate(skill_root: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_root / "SKILL.md"
    receipts_path = skill_root / "receipts.json"
    if not skill_md.is_file():
        return ["SKILL.md missing"]
    if not receipts_path.is_file():
        return ["receipts.json missing"]
    text = skill_md.read_text(encoding="utf-8")
    receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
    evidence = receipts.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        errors.append("receipts.json evidence table missing or empty")
        evidence = {}
    for key, entry in evidence.items():
        refs = entry.get("refs") if isinstance(entry, dict) else None
        if not isinstance(refs, list) or not refs or not all(_ref_ok(r) for r in refs):
            errors.append(f"receipts.json evidence {key!r} has no valid provider refs")
        if not isinstance(entry, dict) or not str(entry.get("claim") or "").strip():
            errors.append(f"receipts.json evidence {key!r} has no claim")

    clause_ids = CLAUSE_RE.findall(text)
    if len(clause_ids) < 8:
        errors.append(f"expected at least 8 clauses, found {len(clause_ids)}")
    if len(clause_ids) != len(set(clause_ids)):
        errors.append("duplicate clause ids")

    sections = CLAUSE_RE.split(text)
    used_evidence: set[str] = set()
    for index in range(1, len(sections), 2):
        clause_id = sections[index]
        body = sections[index + 1]
        body = body.split("\n## ", 1)[0]
        for field in REQUIRED_FIELDS:
            if field not in body:
                errors.append(f"{clause_id}: trigger form incomplete, missing {field!r}")
        match = re.search(r"^- evidence: (.+)$", body, re.M)
        if match:
            for token in (item.strip() for item in match.group(1).split(",")):
                used_evidence.add(token)
                if token not in evidence:
                    errors.append(f"{clause_id}: evidence id {token!r} not in receipts.json")

    for key in evidence:
        if key not in used_evidence:
            errors.append(f"receipts.json evidence {key!r} is bound to no clause")

    if "Non-claims" not in text:
        errors.append("Non-claims section missing")
    if "skills-shared" not in text:
        errors.append("upstream provenance pointer missing")

    # L0 kernel: one domain-free kernel per clause, counts tied.
    kernel_path = skill_root / "references" / "portable-supervision-kernel.md"
    if not kernel_path.is_file():
        errors.append("L0 kernel references/portable-supervision-kernel.md missing")
    else:
        kernel_text = kernel_path.read_text(encoding="utf-8")
        if "L0 procedural" not in kernel_text:
            errors.append("L0 kernel does not declare itself the procedural layer")
        kernels = KERNEL_RE.findall(kernel_text)
        if len(kernels) != len(clause_ids):
            errors.append(
                f"kernel/clause count mismatch: {len(kernels)} kernels vs {len(clause_ids)} clauses"
            )

    # L1 topology: every primitive self-defined and receipt-bound.
    topology_path = skill_root / "domain" / "machine-topology.json"
    if not topology_path.is_file():
        errors.append("L1 domain/machine-topology.json missing")
    else:
        topology = json.loads(topology_path.read_text(encoding="utf-8"))
        primitives = topology.get("primitives")
        if not isinstance(primitives, dict) or not primitives:
            errors.append("topology primitives missing or empty")
        else:
            for name, prim in primitives.items():
                if not isinstance(prim, dict) or not str(prim.get("what") or "").strip() or not str(prim.get("owner") or "").strip():
                    errors.append(f"topology primitive {name!r} lacks what/owner")
                    continue
                prim_evidence = prim.get("evidence")
                if not isinstance(prim_evidence, list) or not prim_evidence:
                    errors.append(f"topology primitive {name!r} carries no evidence ids")
                    continue
                for token in prim_evidence:
                    if token not in evidence:
                        errors.append(f"topology primitive {name!r}: evidence id {token!r} not in receipts.json")

    errors.extend(validate_protocol(skill_root))
    errors.extend(validate_clause_fixtures(skill_root, clause_ids))
    errors.extend(validate_campaigns(skill_root, clause_ids))
    return errors


def validate_protocol(skill_root: Path) -> list[str]:
    """The protocol document exists, carries its caveats, and is reachable from
    every campaign spec.

    Two halves, both load-bearing. Resolving the path is what stops a finding
    from being filed into a name; requiring every campaign spec to name it is
    what puts it in front of the person interpreting a wave, who reads the spec
    and has no reason to open the inventory.
    """
    errors: list[str] = []
    repo_root = skill_root.parents[1]
    behavioral = skill_root / "evals" / "behavioral.json"
    sources: list[tuple[str, Path]] = []
    if behavioral.is_file():
        sources.append(("evals/behavioral.json", behavioral))
    campaigns = skill_root / "evals" / "behavioral-campaigns"
    sources.extend(
        (f"{spec.parent.name}/spec.json", spec)
        for spec in sorted(campaigns.glob("*/spec.json"))
    )
    if not sources:
        return ["no campaign spec or inventory to carry the protocol reference"]

    resolved: set[str] = set()
    for label, path in sources:
        declared = json.loads(path.read_text(encoding="utf-8")).get("protocol")
        if not isinstance(declared, str) or not declared.strip():
            errors.append(f"{label} declares no protocol document")
            continue
        document = repo_root / declared
        if not document.is_file():
            errors.append(
                f"{label} names protocol {declared!r}, which does not exist - "
                "a filed finding with no file is a NO-HOME wearing a path"
            )
            continue
        if declared in resolved:
            continue
        resolved.add(declared)
        text = document.read_text(encoding="utf-8")
        for anchor in PROTOCOL_ANCHORS:
            if anchor not in text:
                errors.append(f"{declared} lost the interpretation-time obligation {anchor!r}")
    return errors


def judge_c7(root: Path) -> list[str]:
    """Which of C7's exit discriminators this escalation fails; empty = compliant.

    C7's written exit is narrow on purpose, and every id below is decided from
    the fixture's own bytes rather than from its name: the escalation names the
    gate and quotes its refusal verbatim, it proves the in-candidate exit
    unavailable instead of asserting it, it asks for an authorization pinned to
    the exact reviewed subject and retired by the landing that spends it, it
    touches no gate file, it is filed where the owner reads it, and the lane
    ends honestly unmerged. Drop the pin or the retirement and the same
    escalation becomes a waiver wearing a type.
    """
    receipt_path = root / "escalation-receipt.json"
    changed_path = root / "changed-files.txt"
    if not receipt_path.is_file() or not changed_path.is_file():
        return ["fixture-not-escalation-shaped"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    changed = [
        line.strip()
        for line in changed_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    authorization = receipt.get("authorization")
    if not isinstance(authorization, dict):
        authorization = {}

    failures: list[str] = []
    gate = str(receipt.get("gate") or "").strip()
    if not gate:
        failures.append("gate-unnamed")
    if not REFUSAL_RE.fullmatch(str(receipt.get("refusal") or "")):
        failures.append("refusal-not-verbatim")
    if not str(receipt.get("structural_reason") or "").strip():
        failures.append("structural-reason-absent")
    if not str(receipt.get("unavailability_probed") or "").strip():
        failures.append("unavailability-assumed-not-proved")
    if not HEX64_RE.fullmatch(str(authorization.get("subject_sha256") or "")):
        failures.append("authorization-not-byte-pinned")
    if not str(authorization.get("retired_by") or "").strip():
        failures.append("authorization-never-retired")
    if gate and gate in changed:
        failures.append("gate-widened")
    if not str(receipt.get("filed_at") or "").strip():
        failures.append("escalation-unfiled")
    if str(receipt.get("lane_exit") or "") != "UNMERGED":
        failures.append("lane-exit-not-honest")
    return failures


def judge_c12(root: Path) -> list[str]:
    """Which of C12's demonstration discriminators this claim fails.

    A claim that records its state as ABSENT is compliant by construction -
    that is the honest exit the clause exists to keep open, and it needs no
    demonstration because it asserts nothing. A claim that says NEGATIVE has
    to have watched its own observer go GREEN on a clean subject and RED on a
    planted violation, and it has to have watched it AT THE SAME CALL SITE
    with the SAME argv: a demonstration through a different access path
    licenses that other path, never this one, which is exactly how a probe
    that cannot see body edits gets vouched for by a surface that can.
    """
    claim_path = root / "claim.json"
    if not claim_path.is_file():
        return ["fixture-not-claim-shaped"]
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    observer = claim.get("observer")
    if not isinstance(observer, dict):
        return ["observer-undeclared"]
    demonstration = observer.get("demonstration")
    if not isinstance(demonstration, dict):
        demonstration = {}

    failures: list[str] = []
    state = str(claim.get("state") or "")
    if state not in ("NEGATIVE", "ABSENT"):
        failures.append("state-not-one-of-negative-absent")
    if not str(claim.get("statement") or "").strip():
        failures.append("claim-unstated")
    if state != "NEGATIVE":
        return failures

    if demonstration.get("clean_subject") != "GREEN":
        failures.append("clean-subject-not-demonstrated-green")
    if demonstration.get("planted_violation") != "RED":
        failures.append("planted-violation-not-demonstrated-red")
    if demonstration.get("call_site") != observer.get("call_site"):
        failures.append("demonstrated-at-a-different-call-site")
    if demonstration.get("argv") != observer.get("argv"):
        failures.append("demonstrated-with-different-flags")
    return failures


CLAUSE_JUDGES = {"C7": judge_c7, "C12": judge_c12}


def validate_clause_fixtures(skill_root: Path, clause_ids: list[str]) -> list[str]:
    """Every clause fixture's declared verdict must be the one a judge computes.

    Both halves are load-bearing. A fixture the judge decides differently than
    the index declares means the clause text and its evidence have drifted
    apart. A clause whose fixtures all point one way means nothing has shown
    the judge can refuse - the same single-arrival defect the campaign's
    permanent negative control exists to close, one layer down.
    """
    errors: list[str] = []
    index_path = skill_root / CLAUSE_FIXTURES / "index.json"
    if not index_path.is_file():
        return [f"clause fixture index {CLAUSE_FIXTURES}/index.json missing"]
    fixtures = json.loads(index_path.read_text(encoding="utf-8")).get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        return ["clause fixture index carries no fixtures"]

    directions: dict[str, set[str]] = {}
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            errors.append("clause fixture entry is not an object")
            continue
        fixture_id = fixture.get("id")
        clause = fixture.get("clause")
        expected = fixture.get("expected")
        if clause not in clause_ids:
            errors.append(
                f"clause fixture {fixture_id!r} names clause {clause!r} absent from SKILL.md"
            )
            continue
        judge = CLAUSE_JUDGES.get(clause)
        if judge is None:
            errors.append(f"clause fixture {fixture_id!r} names clause {clause} with no judge")
            continue
        if expected not in ("compliant", "violating"):
            errors.append(
                f"clause fixture {fixture_id!r} declares expectation {expected!r}, "
                "not 'compliant' or 'violating'"
            )
            continue
        root = skill_root / CLAUSE_FIXTURES / str(fixture.get("path") or "")
        if not root.is_dir():
            errors.append(
                f"clause fixture {fixture_id!r} directory missing: {fixture.get('path')!r}"
            )
            continue
        failed = judge(root)
        verdict = "violating" if failed else "compliant"
        if verdict != expected:
            detail = f" on {','.join(failed)}" if failed else ""
            errors.append(
                f"clause fixture {fixture_id!r} judged {verdict}{detail}, "
                f"declared {expected}"
            )
        directions.setdefault(clause, set()).add(expected)

    for clause in sorted(CLAUSE_JUDGES):
        shown = directions.get(clause, set())
        if shown != {"compliant", "violating"}:
            errors.append(
                f"{clause} fixtures demonstrate only {sorted(shown) or 'nothing'} - a judge "
                "that has never refused has not been shown to be able to"
            )
    return errors


def validate_blind_negative(skill_root: Path, case: dict) -> list[str]:
    """The negative control must be presentable blind.

    The invariant it exists to enforce is: THE JUDGE'S STANDARD HAS REFUSED AT
    LEAST ONE CASE IT COULD NOT HAVE KNOWN TO REFUSE. An input that names its
    own violations measures reading comprehension instead, so the judge-facing
    half is run-shaped and scanned, and the self-describing half lives in a
    sibling answer key the judge never receives (ed3c/skill-concerns#49).
    """
    errors: list[str] = []
    case_id = case.get("id")
    judge_input = case.get("judge_input")
    answer_key = case.get("answer_key")

    if not isinstance(answer_key, str) or not (skill_root / answer_key).is_file():
        errors.append(f"negative control {case_id!r} answer key missing: {answer_key!r}")
    if not isinstance(judge_input, str) or not (skill_root / judge_input).is_dir():
        return errors + [f"negative control {case_id!r} judge input missing: {judge_input!r}"]

    root = skill_root / judge_input
    if isinstance(answer_key, str) and (skill_root / answer_key).resolve().is_relative_to(root.resolve()):
        errors.append(f"negative control {case_id!r} answer key sits inside the judge input")

    workspace = root / "workspace"
    for relative in ("calls.log", "chore.txt", "terminal-state.txt"):
        if not (root / relative).is_file():
            errors.append(f"negative control {case_id!r} is not run-shaped: {relative} missing")
    if not workspace.is_dir():
        return errors + [f"negative control {case_id!r} is not run-shaped: workspace/ missing"]

    for path, token in blind_scan(root):
        errors.append(
            f"negative control {case_id!r} announces itself: giveaway {token!r} in {path} - "
            "it cannot measure a refusal the judge could not have known to make"
        )

    state = root / "terminal-state.txt"
    if state.is_file() and state.read_text(encoding="utf-8") != terminal_state_text(workspace):
        errors.append(
            f"negative control {case_id!r} terminal-state.txt disagrees with its own workspace - "
            "regenerate with scripts/ab_campaign.py negative-control"
        )

    chore = root / "chore.txt"
    if chore.is_file() and chore.read_text(encoding="utf-8").strip() != str(case.get("chore") or "").strip():
        errors.append(f"negative control {case_id!r} chore.txt does not name the case's chore")
    criteria = case.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        errors.append(
            f"negative control {case_id!r} declares no criteria - it would arrive in the batch "
            "as the one run the rubric has no entry for, which is itself a tell"
        )
    return errors


def validate_campaigns(skill_root: Path, clause_ids: list[str]) -> list[str]:
    """Campaign-level gates: the judge keeps a case it must refuse, and every
    judged wave lands in an append-only ledger.

    CI asserts only what is deterministic - that the negative case EXISTS with
    its expected verdict declared and its transcript bytes present. The verdict
    itself is produced by the judge at campaign run time.

    The ledger-non-empty check below means an unseeded skill tree cannot pass
    hermetic validation - it presupposes at least one live campaign has been
    run and its receipt committed once, out of band. That one-time act is a
    bootstrapping precondition, not a runtime dependency: this function still
    only inspects committed bytes and never re-derives or re-judges a verdict,
    so evidence_ceiling stays L3_HERMETIC (same shape as receipts.json's own
    evidence table, which has always required non-empty, host-sourced refs).
    """
    errors: list[str] = []

    behavioral_path = skill_root / "evals" / "behavioral.json"
    if not behavioral_path.is_file():
        errors.append("campaign inventory evals/behavioral.json missing")
    else:
        scenarios = json.loads(behavioral_path.read_text(encoding="utf-8")).get("scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            errors.append("campaign inventory has no scenarios")
            scenarios = []
        negatives = [s for s in scenarios if isinstance(s, dict) and s.get("control") == "negative"]
        if not negatives:
            errors.append(
                "campaign inventory carries no control:negative case - a judge that has never "
                "refused anything is a single arrival, not a physical standard"
            )
        for case in negatives:
            case_id = case.get("id")
            if case.get("expected_verdict") != "violated":
                errors.append(f"negative control {case_id!r} does not declare expected_verdict 'violated'")
            clauses = case.get("clauses")
            if not isinstance(clauses, list) or not clauses:
                errors.append(f"negative control {case_id!r} names no violated clauses")
            else:
                for clause in clauses:
                    if clause not in clause_ids:
                        errors.append(f"negative control {case_id!r} names clause {clause!r} absent from SKILL.md")
            errors.extend(validate_blind_negative(skill_root, case))

    ledger_path = skill_root / "evals" / "behavioral-campaigns" / "ledger.json"
    if not ledger_path.is_file():
        errors.append("cross-wave judge ledger evals/behavioral-campaigns/ledger.json missing")
        return errors
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    entries = ledger.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("judge ledger carries no entries")
        return errors
    previous = GENESIS
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"ledger entry {index} is not an object")
            return errors
        for key in LEDGER_ENTRY_KEYS:
            if not entry.get(key):
                errors.append(f"ledger entry {index} ({entry.get('wave')!r}) missing required key {key!r}")
        if entry.get("prev_sha256") != previous:
            errors.append(
                f"ledger entry {index} breaks the append-only chain: "
                f"prev_sha256 {entry.get('prev_sha256')!r} != {previous!r}"
            )
        previous = entry_digest(entry)
    if ledger.get("head_sha256") != previous:
        errors.append("ledger head_sha256 does not match the last entry - the tail was removed or rewritten")
    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: spatial-loop-grounded clause and receipt bindings intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
