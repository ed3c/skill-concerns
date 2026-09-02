#!/usr/bin/env python3
"""Deterministic validator for the shadow-architect bundle: schemas, ties, scans.

Every check here is either a SCHEMA this bundle owns or a TIE between two places
that must agree, so a hollowed document reds instead of describing a mechanism
that is no longer there:

  clauses    <-> kernel entries                (count-tied, one kernel per clause)
  clauses    <-> precedent ledger ids          (both ways)
  clauses    <-> receipts evidence ids         (every clause cited, every id bound)
  clause provenance line <-> ledger monitor record (verbatim)
  provenance subject commit <-> the fixture's own bytes (the fixture IS that diff)
  precedent detector <-> its own fixture and control (fires there, silent here)
  Diagnostics prose <-> precedent_driver.DIAGNOSTICS  (by name, both ways)
  receipts.json <-> gen_shadow_receipts.render(ledger)  (byte-identical; hand edits red)

The finding schema is NOT re-declared here. `precedent_driver.finding_errors` is
the one declaration, the emitter refuses its own records against it, and this
file calls the same function -- a wrapper here would be a second literal of one
schema, which is the shape clause P3 exists to refuse.

`NO_REACH_IMPORTS` is the reader-only property as a tested surface rather than a
promise: no module in this bundle may import a way to spawn a process or open a
socket. That is the property one level under any list of forbidden verbs -- a
module that cannot run a command cannot file, whatever strings it happens to
hold -- and it is the only form of the check that can cover this file, which
necessarily carries the names it looks for.
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
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

# P3 is this bundle's own clause -- "a second literal of a set that already
# exists" -- and this file carried two of them: a private `HEX40` mirror of the
# commit identity and a fourth copy of the role vocabulary. Both are declared
# once in `scripts/common.py` (ed3c/skill-concerns#112). `skill.json` names
# `../../scripts/common.py` in `shared_contracts`, so the receipt binds the bytes
# these names come from.
from common import HEX40, ROLE_TOKENS, roles_block  # noqa: E402

CLAUSE_RE = re.compile(r"^## (P\d+)\. ", re.M)
KERNEL_RE = re.compile(r"^- (K\d+) ", re.M)
REQUIRED_FIELDS = ("- Signal:", "- Action:", "- Why:", "- provenance:", "- evidence:")
BACKTICKED = re.compile(r"`([^`]+)`")
PROVIDER_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$")
MONITOR_RECORD = re.compile(r"^(?:commit:[0-9a-f]{40}|ledger:[0-9a-z][0-9a-z-]*)$")

# The entry document's `## ` headings, in order. `scripts/check_skill_bundles.py`
# reads this tuple out of these bytes (parsed, never imported) and compares it to
# the document's own headings, so a clause deleted from the entry document reds
# against a file the deletion never touched.
SKILL_MD_CLAUSES = (
    "The precedent ledger - pinned bytes, one wave receipt per clause",
    "Clause form",
    "P1. An abstraction, field or config key no process resolves",
    "P2. Boring over clever: a mechanism that needs an explanation to read as correct",
    "P3. The stale list: a second literal of a set that already exists",
    "P4. Availability is not use: a convention only author memory re-reads",
    "P5. The smallest diff that satisfies the issue, and no gate widened to fit it",
    "P6. A restated copy of another owner's ceremony, where a pointer belongs",
    "P7. Ambient versus admitted: a dependency with no pin and no digest",
    "Diagnostics",
    "Knowledge placement",
    "Non-claims",
)

# No module here may spawn a process or reach the network. This is the reader
# property one level UNDER any verb pattern, and it is what covers this file.
NO_REACH_IMPORTS = {"subprocess", "urllib", "requests", "http", "socket", "ftplib", "os"}
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.M)

# The campaign's planted arm is blind because the driver takes one diff path and
# opens that path only. A script naming the key would end that structurally, so
# the token is refused in every script but this one -- the file that carries the
# name it looks for, and the file the campaign never runs.
ANSWER_KEY_TOKEN = "ANSWER-KEY"
ANSWER_KEY_EXEMPT = "validate_shadow_architect.py"

# The differential is the verb, and it must be grep-verifiable on the page.
NEIGHBOURS = {
    "red-team": "executes falsification experiments",
    "spatial-loop-grounded": "issues clause verdicts over supervised conduct",
    "context-closure-engineering": "compiles and checks one bounded context projection",
    "dynamic-workflow": "classifies runtime liveness of dispatch lanes",
    "arrival-engineering": "audits the capability wiring graph at rest",
}


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


def field(body: str, name: str) -> str:
    match = re.search(rf"^- {name}: (.+)$", body, re.M)
    return match.group(1).strip() if match else ""


def check_clauses(text: str, errors: list[str]) -> dict[str, str]:
    bodies = clause_bodies(text)
    if not bodies:
        errors.append("SKILL.md declares no P-clauses")
    for clause, body in bodies.items():
        for required in REQUIRED_FIELDS:
            if required not in body:
                errors.append(f"{clause}: trigger form incomplete, missing {required!r}")
    return bodies


def check_kernel(skill_root: Path, bodies: dict[str, str], errors: list[str]) -> None:
    path = skill_root / "references" / "portable-architecture-policy.md"
    if not path.is_file():
        errors.append("L0 kernel references/portable-architecture-policy.md missing")
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


def check_ledger_tie(ledger: dict, bodies: dict[str, str], errors: list[str]) -> None:
    declared = [entry.get("id") for entry in ledger.get("precedents") or []]
    if len(declared) != len(set(declared)):
        errors.append("CLAUSE_WITHOUT_PRECEDENT: duplicate precedent id in the ledger")
    for missing in sorted(set(bodies) - set(declared)):
        errors.append(
            f"CLAUSE_WITHOUT_PRECEDENT:{missing}: the entry document declares a clause "
            "the ledger does not ground"
        )
    for extra in sorted(set(declared) - set(bodies)):
        errors.append(
            f"CLAUSE_WITHOUT_PRECEDENT:{extra}: the ledger grounds a precedent no clause "
            "states, so nothing a reader reads carries it"
        )


def check_provenance(skill_root: Path, ledger: dict, errors: list[str]) -> None:
    """A clause is grounded, or it is an opinion with a number on it."""
    for precedent in ledger.get("precedents") or []:
        clause = precedent.get("id") or "<unidentified>"
        provenance = precedent.get("provenance")
        if not isinstance(provenance, dict):
            errors.append(f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: no provenance record")
            continue
        receipts = provenance.get("wave_receipt")
        if not isinstance(receipts, list) or not any(
            isinstance(ref, str) and PROVIDER_REF.fullmatch(ref) for ref in receipts
        ):
            errors.append(
                f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: no provider receipt grounds this "
                "clause, so nothing says which wave found it"
            )
        quote = str(provenance.get("quote") or "").strip()
        if not quote:
            errors.append(
                f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: no monitor quote, so nothing says "
                "what the wave actually found"
            )
        record = str(provenance.get("monitor_record") or "")
        if not MONITOR_RECORD.fullmatch(record):
            errors.append(
                f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: monitor record {record!r} names "
                "neither a commit nor a ledger wave"
            )
        wave = provenance.get("wave")
        if wave is not None and (
            not isinstance(wave, str)
            or wave.lower() not in f"{quote} {record}".lower()
        ):
            errors.append(
                f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: wave label {wave!r} is carried by "
                "neither the quote nor the monitor record, so it is remembered rather "
                "than read back"
            )
        subject = str(provenance.get("subject_commit") or "")
        fixture = skill_root / str(precedent.get("fixture") or "")
        if not HEX40.fullmatch(subject):
            errors.append(
                f"PROVENANCE_RECORD_UNBOUND:{clause}: subject commit {subject!r} is not a "
                "commit identity"
            )
        elif not fixture.is_file():
            errors.append(f"PROVENANCE_RECORD_UNBOUND:{clause}: fixture {fixture.name} absent")
        elif subject not in fixture.read_text(encoding="utf-8", errors="replace"):
            errors.append(
                f"PROVENANCE_RECORD_UNBOUND:{clause}: the fixture's own bytes do not name "
                f"{subject}, so nothing says this diff is that commit's"
            )


def check_provenance_lines(
    ledger: dict, bodies: dict[str, str], errors: list[str]
) -> None:
    """The clause a reader reads names the same record the ledger does."""
    records = {
        entry.get("id"): (entry.get("provenance") or {}).get("monitor_record")
        for entry in ledger.get("precedents") or []
    }
    for clause, body in bodies.items():
        line = field(body, "provenance")
        record = records.get(clause)
        if not line:
            errors.append(f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: no provenance line")
        elif record and record not in line:
            errors.append(
                f"PRECEDENT_WITHOUT_PROVENANCE:{clause}: the clause's provenance line does "
                f"not name the ledger's monitor record {record!r}"
            )


def check_detectors(skill_root: Path, ledger: dict, errors: list[str]) -> None:
    """Every clause fires on its own judged diff and stays silent on the cure.

    A rule nobody ever saw fire is an opinion, and a rule that also fires on the
    diff that cured it detects the subject rather than the shape. Both arms are
    read out of the ledger's own fixture fields, so there is no list here to go
    stale.
    """
    import precedent_driver  # noqa: PLC0415

    for precedent in ledger.get("precedents") or []:
        clause = precedent.get("id") or "<unidentified>"
        fixture = skill_root / str(precedent.get("fixture") or "")
        if not fixture.is_file():
            errors.append(f"PRECEDENT_FIXTURE_SILENT:{clause}: fixture absent")
            continue
        hits = precedent_driver.match(
            precedent, fixture.read_text(encoding="utf-8", errors="replace")
        )
        if not hits:
            errors.append(
                f"PRECEDENT_FIXTURE_SILENT:{clause}: the judged diff that earned this "
                "clause does not raise it"
            )
        quoted = "\n".join(line for _, _, line in hits)
        for needle in precedent.get("reproduces") or []:
            if needle not in quoted:
                errors.append(
                    f"PRECEDENT_FIXTURE_SILENT:{clause}: the finding does not quote the "
                    f"bytes the monitor quoted: {needle[:60]!r}"
                )
        control = precedent.get("control")
        if not control:
            continue
        path = skill_root / str(control)
        if not path.is_file():
            errors.append(f"PRECEDENT_CONTROL_NOISY:{clause}: control absent")
        elif precedent_driver.match(
            precedent, path.read_text(encoding="utf-8", errors="replace")
        ):
            errors.append(
                f"PRECEDENT_CONTROL_NOISY:{clause}: the clause is raised by the diff that "
                "cured it, so it detects the subject rather than the shape"
            )


def check_diagnostic_tie(text: str, errors: list[str]) -> None:
    import precedent_driver  # noqa: PLC0415

    body = section_text(text, "Diagnostics")
    if not body:
        errors.append("SKILL.md has no Diagnostics section")
        return
    documented = {
        token for token in BACKTICKED.findall(body) if re.fullmatch(r"[A-Z][A-Z_]+", token)
    }
    for missing in sorted(set(precedent_driver.DIAGNOSTICS) - documented):
        errors.append(f"Diagnostics section omits a diagnostic the driver emits: {missing}")
    for extra in sorted(documented - set(precedent_driver.DIAGNOSTICS)):
        errors.append(f"Diagnostics section names a diagnostic the driver cannot emit: {extra}")


def check_evidence(bodies: dict[str, str], receipts: dict, errors: list[str]) -> None:
    evidence = receipts.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        errors.append("receipts.json evidence table missing or empty")
        return
    for key in sorted(evidence):
        entry = evidence[key]
        if not isinstance(entry, dict) or not entry.get("refs"):
            errors.append(f"receipts.json evidence {key!r} has no refs")
        elif not str(entry.get("claim") or "").strip():
            errors.append(f"receipts.json evidence {key!r} has no claim")
    cited: set[str] = set()
    for clause, body in bodies.items():
        for token in (item.strip() for item in field(body, "evidence").split(",")):
            if not token:
                continue
            cited.add(token)
            if token not in evidence:
                errors.append(f"{clause}: evidence id {token!r} not in receipts.json")
    for key in sorted(set(evidence) - cited):
        errors.append(f"receipts.json evidence {key!r} is bound to no clause")


def check_receipts_are_produced(skill_root: Path, ledger: dict, errors: list[str]) -> None:
    from gen_shadow_receipts import ReceiptRefused, render  # noqa: PLC0415

    path = skill_root / "receipts.json"
    if not path.is_file():
        errors.append("receipts.json missing")
        return
    try:
        produced = render(ledger)
    except ReceiptRefused as exc:
        errors.append(str(exc))
        return
    if path.read_text(encoding="utf-8") != produced:
        errors.append(
            "receipts.json is not what gen_shadow_receipts.py produces from the ledger - "
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


def check_no_reach(path: Path, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"DRIVER_SURFACE_FORBIDDEN:{path.name}: script absent")
        return
    for module in IMPORT_RE.findall(path.read_text(encoding="utf-8")):
        if module.split(".")[0] in NO_REACH_IMPORTS:
            errors.append(
                f"DRIVER_SURFACE_FORBIDDEN:{path.name}: imports {module!r}; nothing in "
                "this bundle may spawn a process or reach the network"
            )


def check_answer_key_blindness(path: Path, errors: list[str]) -> None:
    if path.is_file() and ANSWER_KEY_TOKEN in path.read_text(encoding="utf-8"):
        errors.append(
            f"ANSWER_KEY_VISIBLE:{path.name}: a script that names the campaign answer key "
            "ends the planted arm's blindness"
        )


def check_boundaries(repo_root: Path, text: str, errors: list[str]) -> None:
    """NOT shared with red-team's, and ed3c/skill-concerns#112 records why.

    #112 read this and red-team's `check_boundaries` as one mechanism copied
    twice. On the landed tree they are not: red-team's scans only the Non-claims
    SECTION, this one scans the whole document, and red-team's carries a
    docstring explaining the narrowing as deliberate. Sharing them means picking
    one, and picking the narrow one silently TIGHTENS this bundle's gate --
    which is an enforcement-shape change with no discriminating measurement
    behind it, exactly what `scripts/cure_authorization.py` exists to refuse.
    `NEIGHBOURS` itself is out of scope for the same reason #112 already
    recorded: membership is a per-bundle judgement about which differentials
    this bundle's Non-claims must state.

    So: two readers of one set, not one mechanism with two copies. If they are
    ever to converge, the measurement that says which scope is right comes
    first.
    """
    for name in NEIGHBOURS:
        if name not in text:
            errors.append(f"Non-claims does not name the neighbour it is not: {name}")
        elif not (repo_root / "skills" / name).is_dir():
            errors.append(f"neighbour {name} named but absent from this tree")


def validate(skill_root: Path, repo_root: Path | None = None) -> list[str]:
    repo_root = repo_root or skill_root.parents[1]
    errors: list[str] = []
    entry = skill_root / "SKILL.md"
    ledger_path = skill_root / "domain" / "precedents.json"
    if not entry.is_file():
        return ["SKILL.md missing"]
    if not ledger_path.is_file():
        return ["domain/precedents.json missing"]
    text = entry.read_text(encoding="utf-8")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    bodies = check_clauses(text, errors)
    check_kernel(skill_root, bodies, errors)
    check_ledger_tie(ledger, bodies, errors)
    check_provenance(skill_root, ledger, errors)
    check_provenance_lines(ledger, bodies, errors)
    check_detectors(skill_root, ledger, errors)
    check_diagnostic_tie(text, errors)
    check_receipts_are_produced(skill_root, ledger, errors)
    check_roles(skill_root, errors)
    check_boundaries(repo_root, text, errors)
    for script in sorted((skill_root / "scripts").glob("*.py")):
        check_no_reach(script, errors)
        if script.name != ANSWER_KEY_EXEMPT:
            check_answer_key_blindness(script, errors)
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
    import cure_authorization  # noqa: PLC0415
    import precedent_driver  # noqa: PLC0415

    real = Path(__file__).resolve().parents[1]
    repo_root = real.parents[1]
    checks: list[tuple[str, bool, str]] = []
    scratch = Path(tempfile.mkdtemp(prefix="shadow-architect-selftest-"))

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
        record(name, any(needle in error for error in errors), f"errors={errors[:2]}")

    def edit_ledger(copy: Path, change) -> None:
        path = copy / "domain" / "precedents.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        change(body)
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

    try:
        record(
            "positive_control_unmutated_copy_passes",
            not validate(fresh(), repo_root),
            f"errors={validate(fresh(), repo_root)[:2]}",
        )

        def drop_kernel(copy: Path) -> None:
            path = copy / "references" / "portable-architecture-policy.md"
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            path.write_text(
                "".join(line for line in lines if not line.startswith("- K7 ")),
                encoding="utf-8",
            )

        mutate("dropped_kernel_entry_breaks_the_count_tie", drop_kernel, "count mismatch")

        mutate(
            "clause_without_provenance_reds",
            lambda copy: edit_ledger(copy, lambda body: body["precedents"][0].pop("provenance")),
            "PRECEDENT_WITHOUT_PROVENANCE:P1",
        )
        mutate(
            "clause_whose_receipt_is_prose_reds",
            lambda copy: edit_ledger(
                copy,
                lambda body: body["precedents"][2]["provenance"].__setitem__(
                    "wave_receipt", ["the wave that found it"]
                ),
            ),
            "PRECEDENT_WITHOUT_PROVENANCE:P3",
        )
        mutate(
            "remembered_wave_label_reds",
            lambda copy: edit_ledger(
                copy,
                lambda body: body["precedents"][3]["provenance"].__setitem__(
                    "wave", "wave-99"
                ),
            ),
            "is carried by neither the quote nor the monitor record",
        )
        mutate(
            "fixture_that_is_not_its_subject_commit_reds",
            lambda copy: edit_ledger(
                copy,
                lambda body: body["precedents"][4]["provenance"].__setitem__(
                    "subject_commit", "0" * 40
                ),
            ),
            "PROVENANCE_RECORD_UNBOUND:P5",
        )
        mutate(
            "clause_whose_own_fixture_is_silent_reds",
            lambda copy: edit_ledger(
                copy,
                lambda body: body["precedents"][1].__setitem__(
                    "signal", [r"a-signal-no-diff-carries"]
                ),
            ),
            "PRECEDENT_FIXTURE_SILENT:P2",
        )
        mutate(
            "clause_raised_by_the_diff_that_cured_it_reds",
            lambda copy: edit_ledger(
                copy, lambda body: body["precedents"][1].__setitem__("acquittal", [])
            ),
            "PRECEDENT_CONTROL_NOISY:P2",
        )

        def unground_a_clause(copy: Path) -> None:
            edit_ledger(copy, lambda body: body["precedents"].pop())

        mutate("clause_with_no_ledger_entry_reds", unground_a_clause, "CLAUSE_WITHOUT_PRECEDENT:P7")

        def hand_edit_receipts(copy: Path) -> None:
            path = copy / "receipts.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            body["evidence"]["P4"]["claim"] = "a nicer sentence"
            path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

        mutate(
            "hand_edited_receipts_red",
            hand_edit_receipts,
            "not what gen_shadow_receipts.py produces",
        )

        def drop_a_diagnostic(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "`SUBJECT_MUTATED`", "SUBJECT_MUTATED"
                ),
                encoding="utf-8",
            )

        mutate("undocumented_diagnostic_reds", drop_a_diagnostic, "omits a diagnostic")

        def move_the_provenance_line(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "- provenance: wave-14 / commit:aaf05089cd7b6e738068561d25e586f938b9b47f",
                    "- provenance: wave-14 / a monitor said so",
                ),
                encoding="utf-8",
            )

        mutate(
            "clause_line_that_names_no_record_reds",
            move_the_provenance_line,
            "does not name the ledger's monitor record",
        )

        def plant_a_reach(copy: Path) -> None:
            path = copy / "scripts" / "precedent_driver.py"
            path.write_text(
                "import subprocess\n" + path.read_text(encoding="utf-8"), encoding="utf-8"
            )

        mutate("planted_process_spawn_reds_the_reach_scan", plant_a_reach, "DRIVER_SURFACE_FORBIDDEN")

        def plant_the_answer_key(copy: Path) -> None:
            path = copy / "scripts" / "gen_shadow_receipts.py"
            path.write_text(
                path.read_text(encoding="utf-8")
                + '\n\nKEY = "evals/fixtures/planted/ANSWER-KEY.md"\n',
                encoding="utf-8",
            )

        mutate("planted_answer_key_reference_reds", plant_the_answer_key, "ANSWER_KEY_VISIBLE")

        def unname_a_neighbour(copy: Path) -> None:
            path = copy / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("dynamic-workflow", "that other one"),
                encoding="utf-8",
            )

        mutate("unnamed_neighbour_reds", unname_a_neighbour, "does not name the neighbour it is not")

        # Schema controls: the driver's own record, and the two shapes a signal
        # must never take -- an unquoted opinion and a verdict with no question.
        ledger = precedent_driver.load_ledger(real)
        report = precedent_driver.run(
            real / "evals/fixtures/waves/wave-17-bootstrap-entry-fields.diff", ledger
        )
        good = report["findings"][0]
        schema = precedent_driver.finding_errors
        record("well_formed_finding_passes_the_schema", not schema(good), "")
        record(
            "finding_with_no_quoted_bytes_reds",
            any("no quoted bytes" in error for error in schema({**good, "quoted": []})),
            "",
        )
        record(
            "finding_with_no_question_reds",
            any(
                "may not issue" in error
                for error in schema({**good, "question": "  "})
            ),
            "",
        )
        record(
            "unadjudicated_precedent_cannot_legislate",
            _refuses(
                precedent_driver,
                ledger,
                {"id": "planted-clause"},
                cure_authorization.DIAGNOSTIC,
            ),
            "",
        )
        record(
            "a_detection_never_legislates",
            _refuses(
                precedent_driver,
                ledger,
                {
                    "id": "planted-detected-clause",
                    "cure_authorization": {
                        "kind": "shadow-detection",
                        "ref": "ed3c/skill-concerns#75",
                    },
                },
                "SHADOW detections never authorize",
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


def _refuses(driver, ledger: dict, candidate: dict, needle: str) -> bool:
    try:
        driver.fold_in(ledger, candidate)
    except driver.BuildRefused as exc:
        return needle in str(exc)
    return False


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
    print(
        "PASS: shadow-architect clause, kernel, provenance, detector, diagnostic, "
        "reach and receipt ties intact"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
