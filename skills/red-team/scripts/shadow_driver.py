#!/usr/bin/env python3
"""The boundary monitor: catalogue-match a bundle, run the falsification, file nothing.

SHADOW half. `--bundle` reads one stage boundary's artifacts - landed diffs,
lane reports, receipts files, issues filed during the wave - matches them
against the pinned catalogue, runs the matched class's experiment, and returns
numbered findings. It has no write verb over the subject at all and proves it
by digesting the bundle before and after the pass; a pass whose digest moved
refuses its own report rather than publishing findings read off a tree
something mutated underneath it. "No findings" is the honest steady state.

The one thing it may write is its own run ledger (`--ledger`), which is not the
subject. That is the skill measuring its own effect: known-class recurrence per
wave must trend to zero as classes gate, and a curve that has not bent after
three post-admission waves is itself a finding delivered to the dispatcher.
`--subject` names the station the pass ran at, so the ledger slices by station
rather than merging two declining curves into one unreadable line.

BUILD half. `--add-class` is the only verb that changes the catalogue, and it
is behind the repository's cure-authorization refusal
(`scripts/cure_authorization.py`, ed3c/skill-concerns#93) with `always=True`:
a catalogue class IS an enforcement shape, so naming the adjudication is not
conditional on which words the class happens to use. A judge verdict that has
not been adjudicated cannot legislate the catalogue.

Intervention boundary, drawn hard: nothing here writes into a subject, files an
issue, comments, or merges. `validate_red_team.FORBIDDEN_SURFACE` scans these
bytes for provider-mutating verbs and reds on one - the reader property is a
tested surface, not a promise. What this driver manufactures is
admission-grade evidence the dispatcher files with: `render_demonstration()`
emits a block that drops verbatim into an issue body's observer-demonstration
section and survives that gate's fence-stripping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import cure_authorization  # noqa: E402
from validate_red_team import finding_errors, signal_errors  # noqa: E402


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__"}

# Each artifact kind is one directory under the bundle. A boundary that carries
# none of a kind is legal - an empty kind must not read as a clean kind.
ARTIFACT_KINDS = ("diffs", "reports", "receipts", "issues")

# Named first, collected second. An emitter writes the NAME; `DIAGNOSTICS`
# exists only for the tie against SKILL.md's Diagnostics section, and a
# positional index into it is one insert away from emitting a diagnostic other
# than the one the line says it emits.
CATALOGUE_CLASS_HIT = "CATALOGUE_CLASS_HIT"
CURVE_NOT_DECLINING = "CURVE_NOT_DECLINING"
SUBJECT_MUTATED = "SUBJECT_MUTATED"
FINDING_MALFORMED = "FINDING_MALFORMED"
SIGNAL_CLASS_UNBOUNDED = "SIGNAL_CLASS_UNBOUNDED"

DIAGNOSTICS = (
    CATALOGUE_CLASS_HIT,
    CURVE_NOT_DECLINING,
    SUBJECT_MUTATED,
    FINDING_MALFORMED,
    SIGNAL_CLASS_UNBOUNDED,
    "CATALOGUE_ENTRY_UNGROUNDED",
    "CATALOGUE_GATE_REFERENCE_ABSENT",
    "CATALOGUE_CLASS_GATED_BUT_ACTIVE",
    "DRIVER_SURFACE_FORBIDDEN",
    "DEMONSTRATION_BLOCK_INCOMPLETE",
    "OBSERVATION_TARGET_UNGROUNDED",
    "CEILING_WITHOUT_SENSOR",
    "STATION_ARRIVAL_UNTIED",
    cure_authorization.DIAGNOSTIC,
)

# The station this pass ran at. It is a string here and a vocabulary in
# `domain/observation-topology.json`: the driver carries what it was told, and
# the validator ties every committed record's subject back to a topology row, so
# a station nobody declared reds at the gate instead of inventing itself in the
# ledger.
DEFAULT_SUBJECT = "wave-boundary"

# The probe surfaces that structurally cannot carry the answer they are cited
# for (ed3c/skill-concerns#83). A claim of absence resting on one of these is
# ABSENT, never NEGATIVE.
BLIND_PROBES = {
    "rest-events-edited": re.compile(r"issues/\d+/(?:events|timeline)"),
}
ABSENCE_CLAIM = re.compile(
    r"(?i)\b(?:no|zero|none|0)\b[^\n]{0,80}\bbody[- ]edit", re.M
)
TYPED_EXIT = "HOST_OBSERVED"
HISTORICAL_FIELD = re.compile(
    r"[\"']?(\w*_(?:evaluated|frozen|pinned))[\"']?\s*[:=]\s*([^\n,]+)"
)
LIVE_READ = re.compile(r"read_text\(|load_json\(|json\.load\(|rev-parse|\bnow\(\)")
DIAGNOSTIC_TOKEN = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")
PATH_TOKEN = re.compile(r"\b(?:[\w.-]+/)+[\w.-]+\.\w+\b")
DECLARED_MECHANISM = ("producer", "gate", "validator", "checker")
ADDED_LINE = re.compile(r"^\+(?!\+\+)(.*)$", re.M)
AUTHORIZATION_NAMED = re.compile(
    r"cure[-_]authorization|"
    + "|".join(re.escape(kind) for kind in cure_authorization.EVIDENCE_KINDS)
)


class BuildRefused(RuntimeError):
    """Raised instead of legislating a catalogue class nobody adjudicated."""


# --------------------------------------------------------------------------
# reading the bundle


def bundle_files(bundle: Path, kind: str) -> list[Path]:
    directory = bundle / kind
    if not directory.is_dir():
        return []
    return [
        path
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not set(path.parts) & SKIP_DIRS
    ]


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def subject(bundle: Path, path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(bundle).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def fingerprint(bundle: Path) -> str:
    digest = hashlib.sha256()
    for kind in ARTIFACT_KINDS:
        for path in bundle_files(bundle, kind):
            digest.update(path.relative_to(bundle).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
            digest.update(b"\n")
    return digest.hexdigest()


# --------------------------------------------------------------------------
# the falsification toolkit: one experiment per catalogue class
#
# Every experiment is a pure reader over the bundle and returns
# (subject, expected, observed) triples. The catalogue names the experiment by
# id and `validate_red_team` ties the two sides both ways, so a class whose
# experiment was deleted reds against bytes the deletion never touched.


def _hit(bundle: Path, path: Path, expected: str, observed: str) -> dict[str, Any]:
    return {"subject": subject(bundle, path), "expected": expected, "observed": observed}


def experiment_blind_observer(bundle: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for kind in ("reports", "issues"):
        for path in bundle_files(bundle, kind):
            text = read(path)
            claim = ABSENCE_CLAIM.search(text)
            if not claim:
                continue
            for probe, pattern in BLIND_PROBES.items():
                match = pattern.search(text)
                if not match:
                    continue
                hits.append(
                    _hit(
                        bundle,
                        path,
                        "an absence claim rests on an observer that has demonstrated both directions",
                        f"the claim {claim.group(0)!r} rests on {probe} ({match.group(0)}), "
                        "a surface that cannot carry a body revision at all",
                    )
                )
    return hits


def experiment_free_exit(bundle: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in bundle_files(bundle, "receipts"):
        try:
            document = json.loads(read(path))
        except json.JSONDecodeError:
            continue
        evidence = document.get("evidence") if isinstance(document, dict) else None
        if not isinstance(evidence, dict) or not evidence:
            continue
        taken = [
            key
            for key, entry in evidence.items()
            if isinstance(entry, dict) and entry.get("producer") == TYPED_EXIT
        ]
        if len(taken) == len(evidence):
            hits.append(
                _hit(
                    bundle,
                    path,
                    "some entry is refused when its ground is only a declaration",
                    f"all {len(evidence)} entries take the {TYPED_EXIT} exit and the file is still green",
                )
            )
    return hits


def experiment_trusted_current_literal(bundle: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for kind in ARTIFACT_KINDS:
        for path in bundle_files(bundle, kind):
            for line in read(path).splitlines():
                match = HISTORICAL_FIELD.search(line)
                if match and LIVE_READ.search(match.group(2)):
                    hits.append(
                        _hit(
                            bundle,
                            path,
                            f"{match.group(1)} is bound to the state it recorded",
                            f"{match.group(1)} is re-derived at run time from {match.group(2).strip()}",
                        )
                    )
    return hits


def experiment_duplicate_discovery(bundle: Path) -> list[dict[str, Any]]:
    """A fingerprint is one diagnostic named against one path ON ONE LINE.

    Line-scoped on purpose: the cross product of every diagnostic in a document
    with every path in it manufactures fingerprints nobody wrote, and a
    duplicate-detector whose duplicates are its own artefacts is the class it
    is looking for.
    """
    seen: dict[str, list[str]] = {}
    order: list[str] = []
    for kind in ARTIFACT_KINDS:
        for path in bundle_files(bundle, kind):
            local = {
                f"{diagnostic}@{target}"
                for line in read(path).splitlines()
                for diagnostic in set(DIAGNOSTIC_TOKEN.findall(line))
                for target in set(PATH_TOKEN.findall(line))
            }
            for key in sorted(local):
                if key not in seen:
                    seen[key] = []
                    order.append(key)
                seen[key].append(path.relative_to(bundle).as_posix())
    hits: list[dict[str, Any]] = []
    for key in order:
        artifacts = seen[key]
        if len(artifacts) < 2:
            continue
        hits.append(
            _hit(
                bundle,
                bundle / artifacts[0],
                "a known defect is read back from where it was filed",
                f"{key} is discovered independently by {', '.join(artifacts)}",
            )
        )
    return hits


def experiment_spec_first_lifecycle(bundle: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in bundle_files(bundle, "receipts"):
        try:
            document = json.loads(read(path))
        except json.JSONDecodeError:
            continue
        for key, value in sorted(_declared_mechanisms(document)):
            if value == TYPED_EXIT or not PATH_TOKEN.fullmatch(value):
                continue
            if (bundle / value).exists():
                continue
            hits.append(
                _hit(
                    bundle,
                    path,
                    f"the {key} a declaration names exists in the tree that declares it",
                    f"{key} names {value}, which is absent",
                )
            )
    return hits


def _declared_mechanisms(document: Any, prefix: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(document, dict):
        for key, value in document.items():
            if key in DECLARED_MECHANISM and isinstance(value, str):
                found.append((f"{prefix}{key}", value))
            else:
                found.extend(_declared_mechanisms(value, f"{prefix}{key}."))
    elif isinstance(document, list):
        for item in document:
            found.extend(_declared_mechanisms(item, prefix))
    return found


def experiment_shape_copying(bundle: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in bundle_files(bundle, "diffs"):
        text = read(path)
        added = "\n".join(ADDED_LINE.findall(text))
        shapes = cure_authorization.shapes_in(added)
        # Detection and acquittal read the SAME bytes. Searching the whole
        # patch for the exculpation while detecting only on added lines lets
        # unchanged context - or a diff that merely touches a file where the
        # word "falsification" appears - acquit a shape it never authorized.
        if not shapes or AUTHORIZATION_NAMED.search(added):
            continue
        hits.append(
            _hit(
                bundle,
                path,
                "an enforcement shape names the measurement that chose it",
                f"the change adds {','.join(shapes)} and names no cure-authorization",
            )
        )
    return hits


EXPERIMENTS: dict[str, Callable[[Path], list[dict[str, Any]]]] = {
    "blind-observer": experiment_blind_observer,
    "free-exit": experiment_free_exit,
    "trusted-current-literal": experiment_trusted_current_literal,
    "duplicate-discovery": experiment_duplicate_discovery,
    "spec-first-lifecycle": experiment_spec_first_lifecycle,
    "shape-copying": experiment_shape_copying,
}


# --------------------------------------------------------------------------
# the boundary run


def sampled_classes(catalogue: dict) -> list[str]:
    """Active classes only. A gated class has a machine catching it already."""
    return [
        entry["id"]
        for entry in catalogue.get("classes", [])
        if isinstance(entry, dict) and entry.get("status") == "active"
    ]


def build_finding(index: int, class_id: str, entry: dict, hit: dict) -> dict[str, Any]:
    return {
        "id": f"F{index:02d}",
        "catalogue_class": class_id,
        "subject": hit["subject"],
        "experiment": {
            "commands": list(entry["falsification"]["recipe"]),
            "expected": hit["expected"],
            "observed": hit["observed"],
        },
        "verdict": "CONFIRMED",
        "both_directions": entry["falsification"]["both_directions"],
    }


def run(
    bundle: Path,
    catalogue: dict,
    wave: str,
    boundary: str,
    only: str | None = None,
    subject_kind: str = DEFAULT_SUBJECT,
) -> dict[str, Any]:
    """One boundary pass. `only` runs a single class's experiment.

    `only` is what a catalogue recipe invokes: a recipe is a falsification for
    ONE class, so it must be able to name that class. It bypasses the
    active/gated filter on purpose - a gated class's recipe still has to run,
    or the lifecycle field would be indistinguishable from a deleted detector.
    """
    bundle = bundle.resolve()
    before = fingerprint(bundle)
    entries = {
        entry["id"]: entry
        for entry in catalogue.get("classes", [])
        if isinstance(entry, dict) and entry.get("id")
    }
    if only is not None:
        if only not in entries:
            raise ValueError(f"no such catalogue class: {only!r}")
        classes = [only]
    else:
        classes = sampled_classes(catalogue)
    findings: list[dict[str, Any]] = []
    hits: dict[str, int] = {}
    novel: list[str] = []
    for class_id in classes:
        experiment = EXPERIMENTS.get(class_id)
        if experiment is None:
            novel.append(class_id)
            continue
        found = experiment(bundle)
        hits[class_id] = len(found)
        for hit in found:
            findings.append(
                build_finding(len(findings) + 1, class_id, entries[class_id], hit)
            )
    after = fingerprint(bundle)

    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "wave": wave,
        "boundary": boundary,
        "subject": subject_kind,
        "bundle": str(bundle),
        "classes_sampled": classes,
        "hits": hits,
        "novel_class_candidates": novel,
        "findings": findings,
        "read_only": {"before": before, "after": after, "held": before == after},
        "outcome": "clean",
    }
    if not report["read_only"]["held"]:
        report["findings"] = []
        report["refusal"] = (
            f"{SUBJECT_MUTATED}:{bundle}: the bundle digest moved {before} -> {after} "
            "during a reader-only pass; this report is untrusted"
        )
        report["outcome"] = "blocked"
        return report
    malformed = [
        f"{finding['id']}:{error}"
        for finding in findings
        for error in finding_errors(finding)
    ]
    if malformed:
        report["refusal"] = f"{FINDING_MALFORMED}:{malformed[0]}"
        report["outcome"] = "blocked"
        return report
    report["outcome"] = "changed" if findings else "clean"
    return report


def ledger_record(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": report["generated_utc"],
        "wave": report["wave"],
        "boundary": report["boundary"],
        "subject": report["subject"],
        "classes_sampled": report["classes_sampled"],
        "hits": report["hits"],
        "novel_class_candidates": report["novel_class_candidates"],
        "judge_gaps": len(report["findings"]),
        "duplicate_blocks": report["hits"].get("duplicate-discovery", 0),
    }


def append_record(ledger: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    appended = dict(ledger)
    appended["records"] = [*ledger.get("records", []), record]
    return appended


def curve(ledger: dict[str, Any]) -> list[tuple[str, int]]:
    """Known-class recurrence per wave, oldest first - the mandated readback."""
    per_wave: dict[str, int] = {}
    order: list[str] = []
    for record in ledger.get("records", []):
        wave = record.get("wave")
        if wave not in per_wave:
            per_wave[wave] = 0
            order.append(wave)
        per_wave[wave] += sum(record.get("hits", {}).values())
    return [(wave, per_wave[wave]) for wave in order]


def curve_finding(ledger: dict[str, Any], waves: int = 3) -> str | None:
    """The instrument reporting its own failure to bend the curve.

    Reported rather than presumed: three post-admission waves whose recurrence
    never falls is a finding ABOUT THE ARCHITECTURE, delivered to the
    dispatcher. Fewer than three waves is not evidence in either direction, so
    it returns None rather than a reassuring green.
    """
    points = curve(ledger)
    if len(points) < waves:
        return None
    recent = [count for _, count in points[-waves:]]
    if recent[-1] < recent[0]:
        return None
    return (
        f"{CURVE_NOT_DECLINING}:{points[-waves][0]}..{points[-1][0]}: known-class recurrence "
        f"{recent} has not declined across {waves} waves; the classes are not gating and "
        "the architecture, not the sampling, is what this reports on"
    )


# --------------------------------------------------------------------------
# handoff: the dispatcher files, the monitor manufactures the evidence


def render_demonstration(finding: dict[str, Any]) -> str:
    """The experiment block, shaped to drop VERBATIM into an issue body.

    No fenced block anywhere. The consumer's admission gate strips fenced
    blocks and HTML comments before it decides whether a section carries an
    authored assertion, so a block that is only a fence arrives at that gate as
    an empty section. Inline backticks survive; fences do not. That is a
    property of the consumer's parser, not a style choice, and the round-trip
    fixture is what keeps it true.
    """
    lines = [
        f"- finding: `{finding['id']}`",
        f"- catalogue class: `{finding['catalogue_class']}`",
        f"- subject: `{finding['subject']['path']}` at sha256 `{finding['subject']['sha256']}`",
    ]
    lines += [f"- command: `{command}`" for command in finding["experiment"]["commands"]]
    lines += [
        f"- expected: {finding['experiment']['expected']}",
        f"- observed: {finding['experiment']['observed']}",
        f"- verdict: {finding['verdict']}",
        f"- both directions: {finding['both_directions']}",
    ]
    return "\n".join(lines)


def escalate(finding: dict[str, Any], severity: str, reason: str) -> dict[str, Any]:
    """A signal to the dispatcher, who holds stop authority. Never a patch."""
    signal = {
        "severity": severity,
        "catalogue_class": finding["catalogue_class"],
        "subject": finding["subject"]["path"],
        "reason": reason,
        "finding": finding["id"],
    }
    errors = signal_errors(signal)
    if errors:
        raise ValueError(f"{SIGNAL_CLASS_UNBOUNDED}:{errors[0]}")
    return signal


# --------------------------------------------------------------------------
# BUILD: the only verb that changes the catalogue


def add_class(catalogue: dict, entry: Any) -> dict:
    """Return the catalogue with `entry` appended, or refuse.

    A catalogue class is an enforcement shape by construction - it is what the
    monitor will legislate against from then on - so the authorization is not
    conditional on which words the entry happens to use (`always=True`).
    """
    if not isinstance(entry, dict) or not entry.get("id"):
        raise BuildRefused("CATALOGUE_ENTRY_UNGROUNDED:<unidentified>:entry has no id")
    class_id = entry["id"]
    if any(existing.get("id") == class_id for existing in catalogue.get("classes", [])):
        raise BuildRefused(f"CATALOGUE_ENTRY_UNGROUNDED:{class_id}:already catalogued")
    cure = cure_authorization.refuse(
        class_id,
        json.dumps({key: value for key, value in entry.items() if key != "cure_authorization"}),
        entry.get("cure_authorization"),
        always=True,
    )
    if cure is not None:
        raise BuildRefused(str(cure))
    grown = dict(catalogue)
    grown["classes"] = [*catalogue.get("classes", []), entry]
    return grown


# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """The option surface, extracted so the validator can run recipes through it.

    Every catalogue recipe that invokes this driver is checked against THIS
    parser (`validate_red_team.check_recipes_parse`), so a recipe naming a flag
    that does not exist reds at validation instead of exiting 2 the first time
    somebody trusts the catalogue enough to run it.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", type=Path, help="SHADOW: one boundary's artifacts")
    parser.add_argument(
        "--catalogue", type=Path, default=SKILL_ROOT / "domain" / "catalogue.json"
    )
    parser.add_argument("--ledger", type=Path, default=SKILL_ROOT / "domain" / "run-ledger.json")
    parser.add_argument("--wave", default="unnamed-wave")
    parser.add_argument("--boundary", default="stage-close")
    parser.add_argument(
        "--subject",
        default=DEFAULT_SUBJECT,
        help="SHADOW: the station this pass ran at, from domain/observation-topology.json",
    )
    parser.add_argument(
        "--class", dest="only", help="SHADOW: run one catalogue class's experiment"
    )
    parser.add_argument("--append-record", action="store_true", help="append this run to the ledger")
    parser.add_argument("--add-class", type=Path, help="BUILD: fold one adjudicated class in")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))

    if args.add_class:
        entry = json.loads(args.add_class.read_text(encoding="utf-8"))
        try:
            grown = add_class(catalogue, entry)
        except BuildRefused as exc:
            print(exc, file=sys.stderr)
            return 2
        args.catalogue.write_text(json.dumps(grown, indent=2) + "\n", encoding="utf-8")
        print(f"catalogued {entry['id']} -> {args.catalogue}")
        return 0

    if not args.bundle:
        parser.error("--bundle is required for a SHADOW pass")
    try:
        report = run(
            args.bundle, catalogue, args.wave, args.boundary, args.only, args.subject
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(
        f"red-team: {report['outcome']} classes={len(report['classes_sampled'])} "
        f"findings={len(report['findings'])}"
    )
    for finding in report["findings"]:
        print(f"  {CATALOGUE_CLASS_HIT} {finding['id']} {finding['catalogue_class']} "
              f"{finding['subject']['path']}")
    if report.get("refusal"):
        print(f"  {report['refusal']}")
    status = {"clean": 0, "changed": 1, "blocked": 2}[report["outcome"]]
    if args.append_record and report["outcome"] != "blocked":
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        ledger = append_record(ledger, ledger_record(report))
        args.ledger.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        print(f"  appended run record -> {args.ledger}")
        bend = curve_finding(ledger)
        if bend:
            # R7 is a finding, so it leaves through the exit code like every
            # other finding. Printed on stdout at status 0 it would be prose
            # no caller consumes - the mention-is-not-execution shape the
            # architecture clause exists to refuse.
            print(f"  {bend}")
            status = max(status, 1)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
