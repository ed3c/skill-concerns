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

The record does not have to be appended in the same breath as the pass, and
until ed3c/skill-concerns#158 it did: `--append-record` was reachable only from
a live pass, so the row had to be written BEFORE the wave landed. Landing is
what destroys the evidence - `land_pr.py` stamps every referenced issue body
and every branch head moves, so re-measuring "the same bundle bytes the monitor
measured" (ed3c/skill-concerns#131's acceptance clause) is not possible
afterwards, and three waves in a row lost their record to that ordering.
`--save-report` persists the producer's own `report` object at the pass, and
`--from-report` derives the row from that artifact through the SAME
`ledger_record()`. `run_id` stays the producer's instant OF THE PASS, carried
in the artifact, so nothing becomes hand-typed and the monotonicity arm keeps
working.

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
SAVED_REPORT_UNGROUNDED = "SAVED_REPORT_UNGROUNDED"

DIAGNOSTICS = (
    CATALOGUE_CLASS_HIT,
    CURVE_NOT_DECLINING,
    SUBJECT_MUTATED,
    FINDING_MALFORMED,
    SIGNAL_CLASS_UNBOUNDED,
    SAVED_REPORT_UNGROUNDED,
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
# for (ed3c/skill-concerns#83), each DISPOSED rather than merely labelled: the
# blind surface, what it cannot see, the sighted surface that can, and that
# surface's own ceiling. A claim of absence resting on a blind one is ABSENT,
# never NEGATIVE.
#
# Naming the replacement is the disposition. A refusal that says only what is
# wrong leaves the next report to re-derive the substitute, and re-deriving it
# is how this probe reached every lane in the first place -- `land_pr.py`
# rewrites the referenced issue's body on every land, so every landed PR
# carries an automation body edit the REST feed reports as zero.
#
# The sighted surface is not free of ceilings and its ceiling is carried here
# rather than assumed, because it is the same absence-read-as-negative shape
# one level down (ed3c/skill-concerns#102).
#
# `pattern` matches the PLACEHOLDER, not just a literal issue number. A lane
# report writes `issues/N/events` or `issues/<n>/events` far more often than it
# writes `issues/72/events`, so a probe anchored on `\d+` was structurally
# silent on the documents this class exists to read -- it matched only the
# fixture the class was filed from. `sighted` is the acquittal that has to come
# with that widening: a document naming the GraphQL surface has DISPOSED of the
# blind one, and firing on it would turn every correct disposition (including
# this module's own, and every lane report that adopted it) into a hit. The
# class is "an absence claim RESTS on a blind observer", never "a document
# mentions one".
#
# The acquittal has to survive the ceiling below becoming MANDATORY. Keyed on
# the bare token `userContentEdits`, it was satisfied by the very sentence
# `scripts/check_second_arrival_ceiling.py` orders every carrier in this tree
# to paste -- a document could be acquitted by quoting the compliance string it
# was told to quote, which acquits boilerplate and measurement alike. So the
# acquittal takes two forms and neither is the compliance string:
#
#   - the SURFACE, `graphql`. Measured across wave 24's four lane reports,
#     that is what a consultation actually writes: twelve groundings read "via
#     authenticated gh api graphql". The ceiling sentence has no `graphql` in
#     it. Keying on the field alone also RED-ED those twelve, because the
#     widened claim half matches their `totalCount=0 -> ABSENT` -- correct
#     dispositions reported as the class they had disposed of.
#   - the CONNECTION, `userContentEdits` other than as the field path
#     `userContentEdits.totalCount`. A document that read the connection names
#     it (`userContentEdits(first:20)`, or bare, as wave 21's L2 wrote it); the
#     ceiling spells the field path, and that spelling is the one every carrier
#     is ordered to carry. The lookahead binds to the path rather than to the
#     sentence's prose on purpose: rewording the ceiling must not silently
#     loosen this.
BLIND_PROBES: dict[str, dict[str, Any]] = {
    "rest-events-edited": {
        "pattern": re.compile(r"issues/[^/\s`\"']+/(?:events|timeline)"),
        "sighted": re.compile(r"(?i)graphql|userContentEdits(?!\.totalCount)"),
        "cannot": (
            "carry a body revision at all: `edited` in that payload is a COMMENT event"
        ),
        "instead": (
            "gh api graphql -f query='{repository(owner:\"OWNER\",name:\"REPO\")"
            "{issue(number:N){userContentEdits(first:20)"
            "{totalCount nodes{editedAt editor{login}}}}}}'"
        ),
        # Quoted verbatim from `scripts/check_second_arrival_ceiling.py`, which
        # owns this sentence for every carrier in the tree. One source line on
        # purpose: implicit string concatenation would put quotes and newlines
        # through the middle of it, and the byte scan that keeps the carriers
        # agreeing reads bytes, not the value they evaluate to.
        "ceiling": (
            "userContentEdits.totalCount counts the ORIGINAL revision: 0 is ABSENT, the first edit moves it 0 -> 2, and every later edit by one (ed3c/skill-concerns#102)"  # noqa: E501
            ". So subtract one before calling anything an edit count, and read "
            "the editor logins in the same query - counted alone, an automation "
            "edit and a hand edit are the same number"
        ),
    },
}
# The vocabulary a lane report ACTUALLY writes, not the vocabulary the class was
# filed in (ed3c/skill-concerns#129). `body[- ]edit` appears in no lane report of
# wave 21: every one of the four wrote `totalCount=0 -> ABSENT`, and the phrase
# the first alternative matches is the fixture's, not theirs. A detector whose
# claim half is silent on every document it is pointed at reports `hits: 1` on
# the fixture the class was filed from and that reads in the run ledger as a
# measurement of the wave.
#
# Three alternatives, and the case rules are the discriminator rather than
# decoration. `ABSENT` and `totalCount` are TYPED - a state and a provider field
# - so they match case-sensitively; the prose alternative stays case-insensitive
# because prose is. That is also what keeps `RECEIPT_PRODUCER_ABSENT` out: `_A`
# carries no word boundary, so a diagnostic name ending in the state's spelling
# is not a claim of absence.
#
# Widening is only safe BECAUSE the `sighted` acquittal above already landed:
# a report that types the third state names the GraphQL surface in the same
# breath and is acquitted before the claim is read, so the discipline #83 asked
# for is not turned into a hit by its own cure. The planted negative in
# `tests/test_red_team.py` is that arm, written in wave-21's own words.
#
# What #129 also asks for and is NOT satisfiable from inside this repository is
# its last clause: replaying the four wave-21 lane reports themselves. Those
# reports never entered the tree, and no fixture here is them - the control runs
# their VOCABULARY, quoted from #129's body, and says so.
ABSENCE_CLAIM = re.compile(
    r"(?i:\b(?:no|zero|none|0)\b[^\n]{0,80}\bbody[- ]edit)"
    r"|totalCount[^\n]{0,20}\b0\b"
    r"|\bABSENT\b",
    re.M,
)
TYPED_EXIT = "HOST_OBSERVED"
HISTORICAL_FIELD = re.compile(
    r"[\"']?(\w*_(?:evaluated|frozen|pinned))[\"']?\s*[:=]\s*([^\n,]+)"
)
LIVE_READ = re.compile(r"read_text\(|load_json\(|json\.load\(|rev-parse|\bnow\(\)")
DIAGNOSTIC_TOKEN = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")
PATH_TOKEN = re.compile(r"\b(?:[\w.-]+/)+[\w.-]+\.\w+\b")

# ed3c/skill-concerns#105. A result payload that declares the work unfinished
# in the certificate's own text, in a slot the harness records as completed.
# Both halves are required and the conjunction is the whole discriminator: a
# full report that narrates a yield it recovered from is a report, and a short
# payload that claims nothing is merely short. Only a payload that says it is
# still alive AND fails the report contract is the class.
YIELD_DECLARATION = re.compile(
    r"(?i)\b(?:still in progress|still running|yielding now|"
    r"(?:not|never) (?:yet )?(?:finished|complete|completed)|"
    r"handing (?:back|off) mid[- ](?:run|flight|task))\b"
)
# The lane report contract's load-bearing blocks, named by the same filing:
# the branch it left, the controls it ran, and the body-digest ledger.
REPORT_CONTRACT_BLOCKS = {
    "branch@sha": re.compile(r"(?i)branch@\S"),
    "controls": re.compile(r"(?i)\bcontrols\b"),
    "body-digest ledger": re.compile(r"(?i)\bdigest ledger\b"),
}
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


def named(bundle: Path) -> str:
    """Repository-relative where it can be, absolute where it cannot.

    A persisted report is committed and read by other people, so a scratch
    path baked into it names a directory only its author ever had. Bundles
    that live outside this tree - a clone, a temporary assembly - keep their
    absolute name, because a relative one would be a lie about where to look.
    """
    root = SKILL_ROOT.parents[1]
    return bundle.relative_to(root).as_posix() if bundle.is_relative_to(root) else str(bundle)


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
            for probe, blind in BLIND_PROBES.items():
                match = blind["pattern"].search(text)
                if not match:
                    continue
                # Disposed, not resting: the document already names the surface
                # that can carry the answer, so citing the blind one is the
                # contrast rather than the ground.
                if blind["sighted"].search(text):
                    continue
                hits.append(
                    _hit(
                        bundle,
                        path,
                        "an absence claim rests on an observer that has demonstrated both directions",
                        f"the claim {claim.group(0)!r} rests on {probe} ({match.group(0)}), "
                        f"a surface that cannot {blind['cannot']}. Read it instead with "
                        f"{blind['instead']} -- {blind['ceiling']}",
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


def experiment_yielded_non_report(bundle: Path) -> list[dict[str, Any]]:
    """A result payload that declares itself alive, in a slot recorded as done.

    The byte length rides in the observed half because it is the measurement
    that made the live case legible - a 117-byte result beside eleven full
    reports - and because a reader who wants to re-run this needs the number
    the recipe's first step prints.
    """
    hits: list[dict[str, Any]] = []
    for path in bundle_files(bundle, "reports"):
        text = read(path)
        declaration = YIELD_DECLARATION.search(text)
        if not declaration:
            continue
        missing = [
            name
            for name, pattern in REPORT_CONTRACT_BLOCKS.items()
            if not pattern.search(text)
        ]
        if not missing:
            continue
        hits.append(
            _hit(
                bundle,
                path,
                "a payload recorded as a completed result satisfies the report contract",
                f"the payload declares {declaration.group(0)!r} in "
                f"{len(text.encode('utf-8'))} bytes and carries none of {missing}, "
                "while the record counts it as one of the completed results",
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
    "yielded-non-report": experiment_yielded_non_report,
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
        "bundle": named(bundle),
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
            f"{SUBJECT_MUTATED}:{named(bundle)}: the bundle digest moved {before} -> {after} "
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
    """One run as a record. `hits` is the measurement; two columns are views.

    `judge_gaps` and `duplicate_blocks` are DERIVED from this record's own
    `hits` - one finding is built per hit, so `judge_gaps` is
    `sum(hits.values())`, and `duplicate_blocks` is the
    `duplicate-discovery` entry under another name. They are kept because the
    ledger is append-only and every committed record carries them, and they are
    named as views here because a reader takes three numbers for three facts
    otherwise (ed3c/skill-concerns#130). `validate_red_team.check_ledger` reds
    on a record whose columns disagree with its own hits, so a hand-triaged
    number typed into a committed record cannot pass as a produced one.
    """
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


# The fields `ledger_record()` reads. Named once so the artifact gate and the
# derivation cannot drift: a saved report missing one of these cannot produce a
# row, and a row is never assembled from anything else.
REPORT_DERIVED_FROM = (
    "generated_utc",
    "wave",
    "boundary",
    "subject",
    "classes_sampled",
    "hits",
    "novel_class_candidates",
    "findings",
)


def saved_report_errors(report: Any) -> list[str]:
    """Why a persisted report may not become a row. Derivation, not provenance.

    Every number a record carries comes from `hits`, and every `hits` entry is
    the length of the finding list the same pass built from it. So the gate
    that lets an artifact through is that the artifact's own halves still
    reconcile: each class's count IS the number of findings naming it, every
    finding passes the schema `finding_errors` owns, the read-only digest pair
    held, the outcome is not `blocked`, and `generated_utc` parses as the
    instant `check_ledger` will require. A number edited into a saved report
    contradicts the findings it was derived from and reds here, which is the
    same refusal ed3c/skill-concerns#130 landed one file downstream.

    What this cannot see is a whole artifact authored by hand that satisfies
    every one of those ties - at one file state a produced report and a
    perfectly consistent forged one are the same bytes.
    That is a structural ceiling. CEILING:hand-authored-report-artifact
    The half that watches it is git history: the artifact is committed at the
    boundary, before the wave's lands, exactly as the ledger's own
    `append_only` sentence leans on history for the rest of its property. The
    phrase and the row id are on ONE line each on purpose - the reflexive rule
    matches per line, so a wrapped admission escapes the very marker it owes.
    """
    if not isinstance(report, dict):
        return ["the artifact is not a report object"]
    if report.get("schema_version") != 1:
        return [f"schema_version {report.get('schema_version')!r} is not 1"]
    missing = [field for field in REPORT_DERIVED_FROM if field not in report]
    if missing:
        return [f"the artifact carries no {missing}"]
    errors: list[str] = []
    if report.get("outcome") == "blocked":
        errors.append(
            f"outcome is 'blocked' ({report.get('refusal')!r}); a pass that refused its "
            "own report does not become a record later either"
        )
    read_only = report.get("read_only")
    if not isinstance(read_only, dict) or read_only.get("held") is not True:
        errors.append(
            "read_only.held is not True; the pass never established that the bundle "
            "stood still under it, so its counts are untrusted whenever they are read"
        )
    try:
        datetime.fromisoformat(str(report["generated_utc"]))
    except ValueError:
        errors.append(
            f"generated_utc {report['generated_utc']!r} is not the producer's ISO-8601 "
            "instant; run_id is derived from this field and is never typed"
        )
    hits = report["hits"]
    findings = report["findings"]
    if not isinstance(hits, dict) or not all(
        isinstance(count, int) for count in hits.values()
    ):
        errors.append("hits is not a table of counts")
        return errors
    if not isinstance(findings, list):
        errors.append("findings is not a list")
        return errors
    counted: dict[str, int] = {class_id: 0 for class_id in hits}
    for position, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append(f"finding {position} is not a record")
            return errors
        for error in finding_errors(finding):
            errors.append(f"{finding.get('id', position)}:{error}")
        class_id = finding.get("catalogue_class")
        if class_id not in counted:
            errors.append(
                f"finding {finding.get('id', position)} names class {class_id!r}, which "
                "the artifact's own hits table does not carry"
            )
            continue
        counted[class_id] += 1
    disagreeing = {
        class_id: (count, counted[class_id])
        for class_id, count in hits.items()
        if count != counted[class_id]
    }
    if disagreeing:
        errors.append(
            f"hits {disagreeing} disagree with the findings the same pass built from "
            "them (recorded, derived); one finding is built per hit, so a count that "
            "differs was typed rather than produced"
        )
    unsampled = sorted(set(hits) - set(report["classes_sampled"] or []))
    if unsampled:
        errors.append(f"hits carries {unsampled}, which classes_sampled does not name")
    return errors


def append_record(ledger: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    appended = dict(ledger)
    appended["records"] = [*ledger.get("records", []), record]
    return appended


def stations(ledger: dict[str, Any]) -> list[str]:
    """The stations this ledger carries, in first-appearance order."""
    found: list[str] = []
    for record in ledger.get("records", []):
        station = record.get("subject")
        if station not in found:
            found.append(station)
    return found


def curve(ledger: dict[str, Any], station: str) -> list[tuple[str, int]]:
    """Known-class recurrence per wave AT ONE STATION, oldest first.

    Sliced, never blended, and the slice is the whole point of the `subject`
    field. Two carriers already declared it - this module's docstring and
    `domain/run-ledger.json`'s `subject_kinds` - while the readback grouped by
    `wave` alone and never opened `subject`, so what R7 reported was
    which-stations-happened-to-run per wave wearing a recurrence label
    (ed3c/skill-concerns#130). Blending is not merely noisy: a station that
    stopped gating hides inside a bigger one that did, and the blended series
    then declines with nothing to report. The planted control in
    `tests/test_red_team.py` is exactly that arm.
    """
    per_wave: dict[str, int] = {}
    order: list[str] = []
    for record in ledger.get("records", []):
        if record.get("subject") != station:
            continue
        wave = record.get("wave")
        if wave not in per_wave:
            per_wave[wave] = 0
            order.append(wave)
        per_wave[wave] += sum(record.get("hits", {}).values())
    return [(wave, per_wave[wave]) for wave in order]


def curve_findings(ledger: dict[str, Any], waves: int = 3) -> list[str]:
    """The instrument reporting its own failure to bend the curve.

    Reported rather than presumed: three post-admission waves whose recurrence
    never falls is a finding ABOUT THE ARCHITECTURE, delivered to the
    dispatcher. Fewer than three waves AT A STATION is not evidence in either
    direction, so that station is skipped rather than answered with a
    reassuring green - and a station with too few points can no longer borrow
    another station's decline to look answered.

    EVERY non-declining station is returned, never the first one found. A
    single-string readback left the second station's silence
    indistinguishable from its absence: the dispatcher saw one diagnostic and
    had nothing telling it another station had been skipped, which is the
    hides-inside-a-bigger-one shape the slicing exists to end, one level up.

    The floor is the DECLARED success state and a strict decline cannot read
    it. `[0, 0, 0]` is a station whose classes are gating; `recent[-1] <
    recent[0]` calls it non-declining forever, so the bundle's own steady
    state ("'No findings' is the honest and expected steady state",
    `AGENTS.md`) would be reported as an architecture failure permanently,
    and per-station slicing multiplies that rather than causing it. A last
    point of zero is a decline to the floor whatever preceded it. `[0, 0, 1]`
    still reports: recurrence coming back off the floor is the event this
    finding exists for.
    """
    findings: list[str] = []
    for station in stations(ledger):
        points = curve(ledger, station)
        if len(points) < waves:
            continue
        recent = [count for _, count in points[-waves:]]
        if recent[-1] < recent[0] or recent[-1] == 0:
            continue
        findings.append(
            f"{CURVE_NOT_DECLINING}:{station}:{points[-waves][0]}..{points[-1][0]}: "
            f"known-class recurrence {recent} has not declined across {waves} waves at "
            "this station; the classes are not gating there and the architecture, not "
            "the sampling, is what this reports on"
        )
    return findings


# --------------------------------------------------------------------------
# handoff: the dispatcher files, the monitor manufactures the evidence


def render_demonstration(finding: dict[str, Any]) -> str:
    """The experiment block, shaped to drop VERBATIM into an issue body.

    No fenced block anywhere -- but the reason this docstring used to give for
    that is dead (ed3c/skill-concerns#137). It said the consumer strips fences
    before deciding whether a section carries an authored assertion, so a block
    that was only a fence arrived empty. Since ed3c/noodles#317 the section this
    block lands in is graded by `sections(body, keep_fences=True)`, the one
    reader upstream marks as fence-preserving, and it is not in REQUIRED_SECTIONS
    for the readers that still strip. Fenced or not, that reader sees this text.

    So the grammar is kept for the weaker reason it can still earn: unfenced
    content is the shape both readers admit, which costs nothing and stops the
    block from depending on which reader receives it. What this block does NOT
    satisfy is the evidence gate #317 added -- two labelled directions running
    the identical invocation with different recorded outputs -- because a finding
    records one transcript and declares its second direction in prose. That is
    ed3c/skill-concerns#148, and `test_a_declared_observer_marker_owes_two_
    discriminating_directions` is where the refusal is measured rather than
    assumed.
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
        tree=SKILL_ROOT.parents[1],
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
    parser.add_argument(
        "--save-report",
        type=Path,
        help="SHADOW: persist this pass's own report object, so its record survives the land",
    )
    parser.add_argument(
        "--from-report",
        type=Path,
        help="derive the ledger row from a persisted report instead of from a fresh pass",
    )
    parser.add_argument("--add-class", type=Path, help="BUILD: fold one adjudicated class in")
    return parser


def _append_and_report(ledger_path: Path, report: dict[str, Any], status: int) -> int:
    """The one place a row reaches the ledger, from a live pass or a saved one.

    Both callers go through `ledger_record()` here rather than each building a
    row, because the whole claim of the persisted path is that it derives the
    SAME row - a second assembly site is where "derived" quietly becomes "also
    derived, differently".
    """
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger = append_record(ledger, ledger_record(report))
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(f"  appended run record -> {ledger_path}")
    bends = curve_findings(ledger)
    for bend in bends:
        # R7 is a finding, so it leaves through the exit code like every other
        # finding. Printed on stdout at status 0 it would be prose no caller
        # consumes - the mention-is-not-execution shape the architecture clause
        # exists to refuse. One line PER station: a second non-declining station
        # that never printed is a station the dispatcher was never told about.
        print(f"  {bend}")
    return max(status, 1) if bends else status


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.from_report:
        if args.bundle:
            parser.error("--from-report derives the row from a pass already taken; it takes no --bundle")
        if not args.append_record:
            parser.error("--from-report is a way to append; pass --append-record with it")
        report = json.loads(args.from_report.read_text(encoding="utf-8"))
        refusals = saved_report_errors(report)
        if refusals:
            print(
                f"{SAVED_REPORT_UNGROUNDED}:{args.from_report}: {refusals[0]}",
                file=sys.stderr,
            )
            return 2
        print(
            f"red-team: persisted classes={len(report['classes_sampled'])} "
            f"findings={len(report['findings'])} run_id={report['generated_utc']}"
        )
        return _append_and_report(args.ledger, report, 1 if report["findings"] else 0)

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
    if args.save_report:
        args.save_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"  persisted report -> {args.save_report}")
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
        status = _append_and_report(args.ledger, report, status)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
