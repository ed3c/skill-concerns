#!/usr/bin/env python3
"""The five-surface island audit driver.

SHADOW half: `--tree`/`--topology` reads a tree and a capability ledger and
emits findings. It has no write verb at all, and proves it by digesting the
audited tree before and after the pass; a pass whose digest moved refuses its
own report rather than publishing findings read off a tree something mutated
underneath it.

BUILD half: `--append-row` is the only verb that writes, it writes only the
topology file it was given, and it REFUSES a row whose receipts do not resolve
(`TOPOLOGY_ROW_WITHOUT_RECEIPT`). There are no aspirational rows.

Why five surfaces and not one: an audit that reads only the import graph has
measured whether the capability is *declared*, which was never the question.
The surface table below is the mechanical form of SKILL.md clause A1, and
`validate_arrival_engineering.py` ties the two together by name and by count -
a surface deleted from either side reds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

# The BUILD cure-authorization refusal is a repository-wide rule with one
# implementation (ed3c/skill-concerns#93). This bundle's BUILD verb consumes
# that implementation rather than carrying a second reading of it, the same way
# `scripts/gen_admission.py` consumes the one stamp surface.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import cure_authorization  # noqa: E402

# surface -> what a consumer arriving through it looks like on disk.
# Order is the reporting order and the order clause A1 lists them in.
SURFACES: dict[str, str] = {
    "imports": "production source that names it (.py .js .ts .sh, outside tests/ and evals/)",
    "value_flow": "a committed artifact something reads back (.json .lock .toml .plist data)",
    "ci": "a gate or workflow whose argv reaches it (.github/, ci, workflow)",
    "adapter": "an installed entrypoint, wrapper, or scheduler job (bin/, Makefile, .plist, ops/)",
    "cli_text": "a documented invocation an agent would actually run (.md)",
}

SOURCE_SUFFIXES = {".py", ".js", ".ts", ".sh"}
ARTIFACT_SUFFIXES = {".json", ".lock", ".toml", ".yaml", ".yml"}
# Named, not numbered. An earlier draft called these L0/L1/L2 and shipped a
# validator clause requiring SKILL.md to disambiguate them from the two other
# axes in this repository that also count from L0 (bundle-anatomy concern
# layers, and `common.EVIDENCE_LEVELS`). Coupling a gate to disambiguation
# prose is the cure for a collision; not colliding is the cure for the cause.
# This axis was the newest and had zero consumers, so it is the one that moved.
LEVELS = ("DECLARED", "EXERCISED", "PRODUCTION")
RECEIPT_KIND_LEVEL = {"bytes": "DECLARED", "exercise": "EXERCISED", "run": "PRODUCTION"}
PROVIDER_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$")
HOST_REF = re.compile(r"^host:\S+$")

DIAGNOSTICS = (
    "CONSUMER_ABSENT",
    "VERB_WITHOUT_CONSUMER",
    "CLAIM_ABOVE_ARRIVAL",
    "CLAIM_BELOW_ARRIVAL",
    "DOCUMENTED_PIN_FALSE",
    "POINTER_DANGLING",
    "TOPOLOGY_ROW_WITHOUT_RECEIPT",
    cure_authorization.DIAGNOSTIC,
)

# The two diagnostics the BUILD append raises. They can never appear in a
# SHADOW report, so the audit's own coverage assertion must exclude them by
# name rather than by remembering one literal.
APPEND_ONLY_DIAGNOSTICS = {"TOPOLOGY_ROW_WITHOUT_RECEIPT", cure_authorization.DIAGNOSTIC}

SKIP_DIRS = {".git", "__pycache__", "node_modules"}


class AppendRefused(RuntimeError):
    """Raised instead of appending a row the ledger cannot stand behind."""


# --------------------------------------------------------------------------
# tree reading


def tree_files(tree: Path) -> list[Path]:
    return [
        path
        for path in sorted(tree.rglob("*"))
        if path.is_file() and not SKIP_DIRS.intersection(path.relative_to(tree).parts)
    ]


def tree_fingerprint(tree: Path) -> str:
    """Did anything under `tree` move during this pass -- nothing more.

    Deliberately NOT `scripts/common.tree_digest`, which is this repository's
    tree *identity* (what an admission receipt pins) and is the only function
    that may carry that name. This one is compared only against itself, minutes
    apart, over a `--tree` that is usually some other repository: it must skip
    `.git` (which mutates on read) and tolerate symlinks, where `common`'s
    file selection keeps `.git` and raises `SYMLINK_FORBIDDEN`. Two functions
    with different file selection may not share one name.
    """
    digest = hashlib.sha256()
    for path in tree_files(tree):
        digest.update(path.relative_to(tree).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def classify_surface(relative: Path) -> str | None:
    """Which consumption surface a file belongs to, or None if it is neither.

    Checked most-specific first: a `.github/workflows/*.yml` is CI, not
    value_flow, and `ops/*.plist` is an adapter, not a committed artifact.
    """
    parts = relative.parts
    suffix = relative.suffix
    if ".github" in parts or "ci" in parts or "workflows" in parts:
        return "ci"
    if "bin" in parts or "ops" in parts or suffix == ".plist" or relative.name == "Makefile":
        return "adapter"
    if suffix == ".md":
        return "cli_text"
    if suffix in SOURCE_SUFFIXES:
        if "tests" in parts or "evals" in parts or "fixtures" in parts:
            return None
        return "imports"
    if suffix in ARTIFACT_SUFFIXES:
        return "value_flow"
    return None


def surface_index(
    tree: Path, exclude: frozenset[str] = frozenset()
) -> dict[str, list[tuple[str, str]]]:
    """surface -> [(relative path, text)] for every file that surface owns.

    `exclude` carries the ledger itself. A topology row names its own exit, and
    the ledger usually lives inside the tree it describes, so counting it as a
    surface would let every row prove its own consumption by existing.
    """
    index: dict[str, list[tuple[str, str]]] = {name: [] for name in SURFACES}
    for path in tree_files(tree):
        relative = path.relative_to(tree)
        if relative.as_posix() in exclude:
            continue
        surface = classify_surface(relative)
        if surface is None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        index[surface].append((relative.as_posix(), text))
    return index


# --------------------------------------------------------------------------
# arrival arithmetic


def receipt_level(receipt: Any, tree: Path) -> str | None:
    """The arrival level this receipt supports, or None when it does not resolve.

    A path-form ref must exist in the tree; a provider or host ref is taken as
    present because resolving it needs a network the hermetic pass does not
    have -- `scripts/maintain_skills.py` is the reader that re-resolves those,
    and an unresolvable one comes back from that sweep as its own finding.
    """
    if not isinstance(receipt, dict):
        return None
    level = RECEIPT_KIND_LEVEL.get(receipt.get("kind"))
    ref = receipt.get("ref")
    if level is None or not isinstance(ref, str) or not ref:
        return None
    if PROVIDER_REF.fullmatch(ref) or HOST_REF.fullmatch(ref):
        return level
    return level if (tree / ref).exists() else None


def supported_arrival(row: dict, tree: Path) -> str | None:
    """The arrival this row's receipts support -- the recorded value's producer.

    `audit_row` ties the recorded `arrival` to this by equality, not by `<=`.
    An over-claim was always a finding; an under-claim used to be invisible,
    which made a permanently-understated row exactly the stale list this
    ledger exists to kill -- accurate only as long as an author remembered.
    """
    levels = [
        level
        for level in (receipt_level(item, tree) for item in row.get("receipts") or [])
        if level is not None
    ]
    return max(levels, key=LEVELS.index) if levels else None


# --------------------------------------------------------------------------
# the audit


def finding(row_id: str, diagnostic: str, subject: str, detail: str, action: str) -> dict:
    return {
        "row": row_id,
        "diagnostic": diagnostic,
        "subject": subject,
        "detail": detail,
        "action": action,
    }


def in_this_tree(value: Any, tree: Path) -> bool:
    """True when `value` names something this pass can actually open."""
    return isinstance(value, str) and bool(value) and (tree / value).exists()


def arrival_mismatch(row: dict, supported: str) -> tuple[str, str, str] | None:
    """(diagnostic, detail, action) when `arrival` is not the derived value.

    One declaration, two readers: the SHADOW driver below and
    `validate_arrival_engineering.check_topology` both call this. A second copy
    of the comparison is how the live audit and the committed-ledger gate come
    to disagree about the same row.
    """
    claimed = row.get("arrival")
    if claimed not in LEVELS:
        return (
            "CLAIM_ABOVE_ARRIVAL",
            f"arrival {claimed!r} is not one of {LEVELS}",
            "record one of DECLARED / EXERCISED / PRODUCTION",
        )
    if claimed == supported:
        return None
    if LEVELS.index(claimed) > LEVELS.index(supported):
        return (
            "CLAIM_ABOVE_ARRIVAL",
            f"records {claimed} while its receipts support only {supported}",
            f"lower the row to {supported}, or add the receipt that would justify {claimed}",
        )
    return (
        "CLAIM_BELOW_ARRIVAL",
        f"records {claimed} while its receipts already support {supported}",
        f"raise the row to {supported}; a row that only ever moves when an author "
        "remembers it is the stale list this ledger exists to kill",
    )


def audit_row(row: dict, tree: Path, index: dict[str, list[tuple[str, str]]]) -> tuple[list[dict], list[dict]]:
    findings: list[dict] = []
    unreachable: list[dict] = []
    row_id = row.get("id") or "<unidentified>"

    supported = supported_arrival(row, tree)
    if supported is None:
        findings.append(
            finding(
                row_id,
                "TOPOLOGY_ROW_WITHOUT_RECEIPT",
                row.get("capability") or row_id,
                "no receipt on this row resolves, so nothing supports any arrival level",
                "give the row a receipt that resolves, or file the intention as an issue instead of a ledger row",
            )
        )
    else:
        mismatch = arrival_mismatch(row, supported)
        if mismatch is not None:
            diagnostic, detail, action = mismatch
            findings.append(
                finding(
                    row_id,
                    diagnostic,
                    row.get("capability") or row_id,
                    detail,
                    action,
                )
            )

    carrier = row.get("carrier")
    if not in_this_tree(carrier, tree):
        unreachable.append(
            {
                "row": row_id,
                "subject": carrier,
                "prerequisite": f"a readable tree containing {carrier!r} (read-only clone)",
            }
        )
    else:
        exit_token = row.get("exit")
        if not isinstance(exit_token, str) or not exit_token:
            findings.append(
                finding(
                    row_id,
                    "CONSUMER_ABSENT",
                    carrier,
                    "the row declares no exit at all: there is no way for a consumer to arrive",
                    "expose an exit and bind it, or record the capability as deliberately internal",
                )
            )
        else:
            # The carrier is excluded from its own consumer search: a
            # definition is not a consumption, and a file that names the verb
            # it defines would otherwise prove its own arrival by existing.
            reached = sorted(
                surface
                for surface, entries in index.items()
                if any(exit_token in text for path, text in entries if path != carrier)
            )
            if not reached:
                findings.append(
                    finding(
                        row_id,
                        "CONSUMER_ABSENT",
                        exit_token,
                        f"none of the five surfaces names it: {', '.join(SURFACES)}",
                        "bind the exit to a surface a consumer already traverses",
                    )
                )
            elif not row.get("bound_exit"):
                findings.append(
                    finding(
                        row_id,
                        "VERB_WITHOUT_CONSUMER",
                        exit_token,
                        f"named on {', '.join(reached)} but bound to no exit a consumer traverses",
                        "bind it to a shared exit and make the consumer's receipt inadmissible without it",
                    )
                )

    pin = row.get("documented_pin")
    if isinstance(pin, dict):
        claim_in = pin.get("claim_in")
        expects = pin.get("expects")
        if pin.get("tree") not in (None, "self"):
            # A same-named path in the wrong tree is the worst possible
            # reader: it would answer a question about another repository
            # with this one's bytes.
            unreachable.append(
                {
                    "row": row_id,
                    "subject": claim_in,
                    "prerequisite": f"a readable {pin.get('tree')!r} tree (read-only clone)",
                }
            )
        elif not in_this_tree(claim_in, tree):
            unreachable.append(
                {
                    "row": row_id,
                    "subject": claim_in,
                    "prerequisite": f"a readable tree containing {claim_in!r} (read-only clone)",
                }
            )
        elif not isinstance(expects, str) or expects not in (tree / claim_in).read_text(
            encoding="utf-8", errors="replace"
        ):
            findings.append(
                finding(
                    row_id,
                    "DOCUMENTED_PIN_FALSE",
                    str(claim_in),
                    f"the claim says {expects!r} is recorded there; its bytes do not carry it",
                    "correct the claim or record the value; a pin whose target lacks it retires suspicion and nothing else",
                )
            )

    pointer = row.get("pointer")
    if isinstance(pointer, dict):
        target = pointer.get("target")
        if pointer.get("tree") not in (None, "self"):
            unreachable.append(
                {
                    "row": row_id,
                    "subject": target,
                    "prerequisite": f"a readable {pointer.get('tree')!r} tree (read-only clone)",
                }
            )
        elif not in_this_tree(target, tree):
            findings.append(
                finding(
                    row_id,
                    "POINTER_DANGLING",
                    str(target),
                    "the pointer names something this tree does not contain",
                    "re-anchor the pointer on a live target, or retire the row with its carrier",
                )
            )

    return findings, unreachable


def audit(
    tree: Path, topology: dict, topology_path: Path | None = None, index_fn=surface_index
) -> dict:
    """Audit `tree` against `topology`, reading only.

    `index_fn` exists so the selftest can plant a reader that writes: the
    read-only guard is only a guard if something has been observed tripping
    it, and nothing else in this module can move the tree mid-pass.
    """
    tree = tree.resolve()
    exclude: frozenset[str] = frozenset()
    if topology_path is not None:
        resolved = topology_path.resolve()
        if resolved.is_relative_to(tree):
            exclude = frozenset({resolved.relative_to(tree).as_posix()})
    before = tree_fingerprint(tree)
    index = index_fn(tree, exclude)
    findings: list[dict] = []
    unreachable: list[dict] = []
    rows = topology.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("TOPOLOGY_ROWS_NOT_LIST")
    for row in rows:
        if not isinstance(row, dict):
            raise SystemExit("TOPOLOGY_ROW_NOT_OBJECT")
        row_findings, row_unreachable = audit_row(row, tree, index)
        findings.extend(row_findings)
        unreachable.extend(row_unreachable)
    after = tree_fingerprint(tree)
    report = {
        "schema_version": 1,
        "mode": "shadow",
        "tree": str(tree),
        "rows": len(rows),
        "surfaces": {name: len(index[name]) for name in SURFACES},
        "findings": findings,
        "unreachable": unreachable,
        "read_only": {"digest_before": before, "digest_after": after, "held": before == after},
    }
    if not report["read_only"]["held"]:
        # A reader that moved its subject cannot vouch for what it read.
        report["findings"] = [
            finding(
                "<pass>",
                "CONSUMER_ABSENT",
                str(tree),
                f"a SHADOW pass has no write verb, yet the tree digest moved {before} -> {after}",
                "treat this run's report as untrusted; the audit must not write to the tree it audits",
            )
        ]
        report["outcome"] = "blocked"
    else:
        report["outcome"] = "changed" if findings else "clean"
    return report


# --------------------------------------------------------------------------
# BUILD: the only verb that writes


def append_row(topology: dict, row: Any, tree: Path) -> dict:
    """Return the topology with `row` appended, or refuse.

    Continuous intake: each adjudication that names an automation need becomes
    one row here. The refusal is what keeps it a ledger rather than a backlog -
    a row nothing can re-read is an intention, and intentions belong on issues.

    Two refusals, and they are about different things. A row without a receipt
    is aspirational. A row that introduces or alters an ENFORCEMENT shape and
    names no cure-authorization is unadjudicated - it may be perfectly true and
    still be the copy-nearest-shape error (ed3c/skill-concerns#93), so the row
    carries `cure_authorization` and the decision is the shared one.
    """
    if not isinstance(row, dict) or not row.get("id"):
        raise AppendRefused("TOPOLOGY_ROW_WITHOUT_RECEIPT:<unidentified>:row has no id")
    row_id = row["id"]
    if any(existing.get("id") == row_id for existing in topology.get("rows", [])):
        raise AppendRefused(f"TOPOLOGY_ROW_DUPLICATE:{row_id}")
    cure = cure_authorization.refuse(
        row_id,
        json.dumps({key: value for key, value in row.items() if key != "cure_authorization"}),
        row.get("cure_authorization"),
        tree=tree,
    )
    if cure is not None:
        raise AppendRefused(str(cure))
    if supported_arrival(row, tree) is None:
        raise AppendRefused(
            f"TOPOLOGY_ROW_WITHOUT_RECEIPT:{row_id}:no receipt resolves, so no arrival level is supported"
        )
    appended = dict(topology)
    appended["rows"] = [*topology.get("rows", []), row]
    return appended


# --------------------------------------------------------------------------
# selftest: the planted islands must be found, the controls must not be


def selftest() -> int:
    skill_root = Path(__file__).resolve().parents[1]
    checks: list[tuple[str, bool, str]] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append((name, passed, detail))

    def load(fixture: str) -> tuple[Path, dict, Path]:
        tree = skill_root / "evals" / "fixtures" / fixture
        path = tree / "capabilities.json"
        return tree, json.loads(path.read_text(encoding="utf-8")), path

    planted_tree, planted, planted_path = load("planted")
    before = tree_fingerprint(planted_tree)
    report = audit(planted_tree, planted, planted_path)
    seen = {item["diagnostic"] for item in report["findings"]}
    expected = set(DIAGNOSTICS) - APPEND_ONLY_DIAGNOSTICS
    record(
        "every_planted_island_class_is_detected",
        expected <= seen,
        f"missing={sorted(expected - seen)} seen={sorted(seen)}",
    )
    record(
        "the_audit_invents_no_class_it_cannot_name",
        seen <= set(DIAGNOSTICS),
        f"unknown={sorted(seen - set(DIAGNOSTICS))}",
    )
    record(
        "planted_fixture_is_never_repaired_by_the_audit",
        tree_fingerprint(planted_tree) == before,
        f"digest={before}",
    )
    record(
        "read_only_guard_reports_it_held",
        report["read_only"]["held"] and report["outcome"] == "changed",
        f"outcome={report['outcome']} held={report['read_only']['held']}",
    )

    clean_tree, clean, clean_path = load("clean")
    control = audit(clean_tree, clean, clean_path)
    record(
        "negative_controls_are_not_flagged",
        control["outcome"] == "clean" and not control["findings"],
        f"outcome={control['outcome']} findings={[f['diagnostic'] for f in control['findings']]}",
    )
    record(
        "negative_controls_are_not_vacuous",
        len(clean["rows"]) >= 2 and all(row.get("receipts") for row in clean["rows"]),
        f"rows={[row['id'] for row in clean['rows']]}",
    )

    # Planted defect on the instrument: with the surface index emptied, the
    # properly bound control must go red. A detector that cannot fail on a
    # control it should pass is measuring nothing.
    blinded = audit_row(clean["rows"][0], clean_tree, {name: [] for name in SURFACES})[0]
    record(
        "blinded_instrument_reds_on_the_positive_control",
        any(item["diagnostic"] == "CONSUMER_ABSENT" for item in blinded),
        f"findings={[item['diagnostic'] for item in blinded]}",
    )

    # BUILD half: the append refusal, and its own positive control.
    receiptless = {"id": "planted-aspirational-row", "capability": "a thing we mean to do", "arrival": "PRODUCTION"}
    try:
        append_row(clean, receiptless, clean_tree)
        record("receiptless_row_is_refused_at_append", False, "append returned instead of refusing")
    except AppendRefused as exc:
        record(
            "receiptless_row_is_refused_at_append",
            str(exc).startswith("TOPOLOGY_ROW_WITHOUT_RECEIPT:planted-aspirational-row"),
            str(exc),
        )
    receipted = {
        "id": "planted-receipted-row",
        "capability": "a thing with a receipt",
        "carrier": "capabilities.json",
        "exit": None,
        "bound_exit": None,
        "arrival": "DECLARED",
        "receipts": [{"kind": "bytes", "ref": "ed3c/skill-concerns#73"}],
    }
    clean_before = tree_fingerprint(clean_tree)
    grown = append_row(clean, receipted, clean_tree)
    record(
        "receipted_row_appends",
        len(grown["rows"]) == len(clean["rows"]) + 1,
        f"rows {len(clean['rows'])} -> {len(grown['rows'])}",
    )
    record(
        "append_returns_a_new_ledger_and_writes_nothing",
        tree_fingerprint(clean_tree) == clean_before,
        "append_row is pure; only --append-row writes, and only the file it was given",
    )

    # BUILD, ed3c/skill-concerns#93: the canonical refused case. A row that is
    # fully receipted and would otherwise append, refused because the shape it
    # carries was copied rather than measured.
    ratchet_row = {
        "id": "planted-copied-ratchet-row",
        "capability": cure_authorization.COPY_NEAREST_RATCHET,
        "carrier": "capabilities.json",
        "exit": None,
        "bound_exit": None,
        "arrival": "DECLARED",
        "receipts": [{"kind": "bytes", "ref": "ed3c/skill-concerns#93"}],
    }
    try:
        append_row(clean, ratchet_row, clean_tree)
        record("unauthorized_enforcement_shape_is_refused", False, "append returned instead of refusing")
    except AppendRefused as exc:
        record(
            "unauthorized_enforcement_shape_is_refused",
            str(exc).startswith(f"{cure_authorization.DIAGNOSTIC}:planted-copied-ratchet-row"),
            str(exc),
        )
    # Planted negative control: the SAME row with a named adjudication appends.
    # Without this arm the refusal above could be a gate that refuses every row.
    authorized_row = {
        **ratchet_row,
        "id": "planted-adjudicated-ratchet-row",
        "cure_authorization": dict(cure_authorization.ADJUDICATED_AUTHORIZATION),
    }
    try:
        adjudicated = append_row(clean, authorized_row, clean_tree)
        record(
            "an_adjudicated_enforcement_shape_appends",
            len(adjudicated["rows"]) == len(clean["rows"]) + 1,
            f"rows {len(clean['rows'])} -> {len(adjudicated['rows'])}",
        )
    except AppendRefused as exc:
        record("an_adjudicated_enforcement_shape_appends", False, str(exc))
    # A SHADOW detection is where adjudication starts, not a license to cure.
    try:
        append_row(
            clean,
            {**authorized_row, "cure_authorization": {"kind": "shadow-detection", "ref": "ed3c/skill-concerns#93"}},
            clean_tree,
        )
        record("a_shadow_detection_never_authorizes_a_row", False, "append returned instead of refusing")
    except AppendRefused as exc:
        record(
            "a_shadow_detection_never_authorizes_a_row",
            "SHADOW detections never authorize" in str(exc),
            str(exc),
        )

    # A SHADOW pass that mutated its subject must refuse its own report.
    scratch = Path(tempfile.mkdtemp(prefix="arrival-audit-selftest-"))
    try:
        copy = scratch / "tree"
        shutil.copytree(clean_tree, copy)

        def planted_reader_that_writes(
            tree: Path, exclude: frozenset[str] = frozenset()
        ) -> dict[str, list[tuple[str, str]]]:
            (tree / "PLANTED_SHADOW_WRITE.txt").write_text(
                "a reader must never write here\n", encoding="utf-8"
            )
            return surface_index(tree, exclude)

        mutated = audit(copy, clean, index_fn=planted_reader_that_writes)
        record(
            "planted_shadow_write_refuses_its_own_report",
            mutated["outcome"] == "blocked" and not mutated["read_only"]["held"],
            f"outcome={mutated['outcome']} held={mutated['read_only']['held']}",
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
    print("selftest OK: planted islands found, controls clean, append refuses receipt-less rows")
    return 0


def main(argv: list[str] | None = None) -> int:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", type=Path, default=skill_root.parents[1])
    parser.add_argument("--topology", type=Path, default=skill_root / "domain" / "capability-topology.json")
    parser.add_argument("--append-row", type=Path, help="BUILD: append this row file to --topology")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    topology = json.loads(args.topology.read_text(encoding="utf-8"))

    if args.append_row:
        row = json.loads(args.append_row.read_text(encoding="utf-8"))
        try:
            grown = append_row(topology, row, args.tree.resolve())
        except AppendRefused as exc:
            print(exc, file=sys.stderr)
            return 2
        args.topology.write_text(json.dumps(grown, indent=2) + "\n", encoding="utf-8")
        print(f"appended {row['id']} -> {args.topology}")
        return 0

    report = audit(args.tree, topology, args.topology)
    print(
        f"arrival-audit: {report['outcome']} rows={report['rows']} "
        f"findings={len(report['findings'])} unreachable={len(report['unreachable'])}"
    )
    for item in report["findings"]:
        print(f"  {item['diagnostic']} {item['row']}:{item['subject']} :: {item['action']}")
    for item in report["unreachable"]:
        print(f"  UNREACHABLE {item['row']}:{item['subject']} needs {item['prerequisite']}")
    return {"clean": 0, "changed": 1, "blocked": 2}[report["outcome"]]


if __name__ == "__main__":
    raise SystemExit(main())
