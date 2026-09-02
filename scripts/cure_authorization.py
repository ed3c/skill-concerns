#!/usr/bin/env python3
"""The one BUILD cure-authorization refusal, shared by every BUILD carrier.

ed3c/skill-concerns#93. One lane copied the nearest successful enforcement
precedent - a report-only metric plus a monotonic ratchet - into a new debt
issue "mirroring" the elder's claim; the successor atom then measured three
candidates and proved the copied shape wrong, because a blanket growth bound
misjudges every normal test addition as architectural regression. Cure-shape
selection therefore needs a discriminating measurement BEFORE the shape is
chosen, and a BUILD verb that auto-proposes cures for detected patterns
automates exactly that copy-nearest-shape error.

So: a BUILD proposal that introduces or alters an enforcement shape must NAME
its cure-authorization, and a proposal without one is refused here rather than
in each carrier. Two carriers consume this module today - the maintain loop's
opt-in write verb and `skills/arrival-engineering`'s topology append - and they
consume the same `refuse()`, not two readings of one rule. There is no second
copy of the check; `tests/test_repository_controls.py` is the mechanical reader
for that claim.

Detection is fail-closed by construction. `SHAPES` is a closed vocabulary of
five words, matched on word boundaries over the proposal's ADDED lines only. A
false positive costs one named authorization; a false negative ships an
unadjudicated enforcement shape, which is the failure this module exists to
prevent. That asymmetry is the reason the scan is deliberately blunt.

SHADOW detections never authorize. A detection is the beginning of an
adjudication, not a license to cure, so `shadow-detection` is refused by name
rather than falling through the unknown-kind branch as if someone had typo'd.

An `operator:` ref used to be `any date plus any non-empty text`
(ed3c/skill-concerns#103). The wave-19 judge ran three garbage refs through it
on landed main and all three passed, including
`operator:2026-09-01:the vibes were good`: the gate refused ABSENCE and refused
shadow-detection by name, then admitted every well-formed string forever - no
expiry, no pinned subject, no re-resolver. By this repository's own definition
that is a typed exit with no expiry, no pinned subject and no refusal, which is
the free-exit class, inside the instrument that names it. So an operator
authorization now RESOLVES rather than parses: it names a pinned subject that
exists in the tree and that its own ref repeats, and it carries either an issue
whose body holds the adjudication - a provider ref the cadence sweep
re-resolves - or an inline record with an expiry or a re-resolution cadence. A
ref that is well-formed and resolves to nothing is refused, and an expired
inline record is refused AS EXPIRED, which is a different state from malformed.

What is still not judged here is the QUALITY of the adjudication the artifact
holds. That gap is registered with a sensor and a trigger in
`skills/red-team/domain/residual-sensor-register.json`, not left as a sentence.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple


DIAGNOSTIC = "BUILD_CURE_UNAUTHORIZED"
RULE = (
    "BUILD carries only adjudicated cures: an enforcement shape must name a "
    "cure-authorization whose evidence is a discriminating measurement, a "
    "falsification, or an operator adjudication (ed3c/skill-concerns#93)"
)
ACTION = (
    "measure the invariant and falsify the candidate models first, then name "
    "the issue or adjudication that carries that evidence as the proposal's "
    "cure-authorization"
)

# The five enforcement shapes ed3c/skill-concerns#93 names, and nothing else.
# Word-boundary matched: `gate_ref` is a field name, not a gate being introduced.
SHAPES: dict[str, re.Pattern[str]] = {
    "gate": re.compile(r"\bgat(?:e|es|ed|ing)\b", re.I),
    "ratchet": re.compile(r"\bratchet(?:s|ed|ing)?\b", re.I),
    "threshold": re.compile(r"\bthreshold(?:s)?\b", re.I),
    "refusal": re.compile(r"\brefus(?:al|als|e|es|ed|ing)\b", re.I),
    "escape-hatch": re.compile(r"\bescape[-_ ]hatch(?:es)?\b", re.I),
}

# What an authorization may claim, and what a ref for that claim must look like.
# The ref form is the LABEL. For an operator adjudication it is necessary and
# nowhere near sufficient: `operator_errors` is what makes the label resolve.
PROVIDER_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$")
OPERATOR_REF = re.compile(r"^operator:\d{4}-\d{2}-\d{2}:\S.*$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OPERATOR_KIND = "operator-adjudication"
EVIDENCE_KINDS: dict[str, re.Pattern[str]] = {
    "discriminating-measurement": PROVIDER_REF,
    "falsification": PROVIDER_REF,
    OPERATOR_KIND: OPERATOR_REF,
}
SHADOW_KIND = "shadow-detection"
# The judge's exact garbage ref, kept here so every carrier's planted control
# measures the same bytes instead of a paraphrase of them.
VIBES_REF = "operator:2026-09-01:the vibes were good"

# The canonical refused case from the trigger chain, kept here so both carriers'
# planted controls measure the same bytes instead of two paraphrases of them.
COPY_NEAREST_RATCHET = (
    '{"control": "max_tracked_files", '
    '"shape": "monotonic ratchet copied from the nearest successful precedent", '
    '"threshold": 36, '
    '"note": "any increase is refused as architectural regression"}'
)
ADJUDICATED_AUTHORIZATION = {
    "kind": "discriminating-measurement",
    "ref": "ed3c/skill-concerns#93",
}


class Refusal(NamedTuple):
    """One refusal, rendered by whichever carrier raised it."""

    diagnostic: str
    subject: str
    detail: str
    action: str

    def __str__(self) -> str:
        return f"{self.diagnostic}:{self.subject}:{self.detail}"


def shapes_in(text: str) -> list[str]:
    """Which enforcement shapes `text` introduces or alters, in declared order."""
    return [name for name, pattern in SHAPES.items() if pattern.search(text or "")]


def operator_errors(
    authorization: dict, tree: Path | None, today: date
) -> list[str]:
    """Everything that stops an operator ref from RESOLVING, or an empty list.

    Two states this deliberately keeps apart, because a caller acts on them
    differently: malformed (the record never named an artifact) and expired
    (it named one and the clock ran out). An exit whose absence and whose
    lapse look the same in the bytes is the shape ed3c/skill-concerns#103 filed.
    """
    errors: list[str] = []
    subject = authorization.get("subject")
    if not isinstance(subject, str) or not subject.strip():
        # Reported, never returned early: a ref like the judge's
        # `operator:2026-09-01:the vibes were good` is missing the subject AND
        # the artifact, and a diagnostic that named only the first would send
        # the next author back for a second round on the same record.
        errors.append(
            "operator adjudication names no pinned subject; an operator ref "
            "without one is a date and a sentence, and any sentence satisfies it"
        )
    else:
        if subject not in str(authorization.get("ref") or ""):
            errors.append(
                f"operator ref does not name its own pinned subject {subject!r}, so the "
                "sentence and the field are free to drift apart"
            )
        target = subject.split("#", 1)[0]
        if tree is None:
            errors.append(
                f"operator adjudication pins subject {target!r} and no tree was given to "
                "resolve it against; absence of a tree is refused rather than skipped"
            )
        elif not (tree / target).exists():
            errors.append(
                f"operator adjudication pins subject {target!r}, which does not exist in "
                "the tree; a pinned subject that resolves to nothing pins nothing"
            )
    adjudication = authorization.get("adjudication")
    if not isinstance(adjudication, dict) or not adjudication:
        return errors + [
            "operator adjudication names no adjudication artifact: carry "
            "adjudication.issue as a provider ref whose body holds it, or an inline "
            "adjudication.record with an expiry or a re-resolution cadence"
        ]
    issue = adjudication.get("issue")
    record = adjudication.get("record")
    if issue and record:
        errors.append(
            "operator adjudication carries both an issue and an inline record; "
            "exactly one artifact is the adjudication"
        )
    elif issue:
        if not isinstance(issue, str) or not PROVIDER_REF.fullmatch(issue):
            errors.append(
                f"operator adjudication issue {issue!r} does not carry the provider "
                f"form {PROVIDER_REF.pattern}, so nothing can re-resolve it"
            )
    elif isinstance(record, str) and record.strip():
        expires = adjudication.get("expires")
        cadence = adjudication.get("re_resolve")
        if not expires and not (isinstance(cadence, str) and cadence.strip()):
            errors.append(
                "inline operator adjudication carries neither an expiry nor a "
                "re-resolution cadence, which is the free exit this rule closes"
            )
        elif expires is not None:
            if not isinstance(expires, str) or not ISO_DATE.fullmatch(expires):
                errors.append(
                    f"inline operator adjudication expiry {expires!r} is not an "
                    "ISO-8601 date"
                )
            elif date.fromisoformat(expires) < today:
                errors.append(
                    f"inline operator adjudication expired on {expires}; it is not "
                    "malformed, it lapsed, and a lapsed adjudication authorizes nothing"
                )
    else:
        errors.append(
            "operator adjudication names no adjudication artifact: carry "
            "adjudication.issue as a provider ref whose body holds it, or an inline "
            "adjudication.record with an expiry or a re-resolution cadence"
        )
    return errors


def authorization_errors(
    authorization: Any, *, tree: Path | None = None, today: date | None = None
) -> list[str]:
    """Everything wrong with an authorization record, or an empty list.

    Provider-ref kinds stay shape-only: whether the named issue's body really
    carries the measurement is the reviewer's read at landing time, and the
    cadence sweep is what re-resolves the ref itself. The operator kind is not
    shape-only any more - it must resolve (`operator_errors`), because a form
    that admits every well-formed sentence forever is the free-exit class this
    repository catalogues.
    """
    if not isinstance(authorization, dict):
        return [f"cure-authorization is not a record: {authorization!r}"]
    kind = authorization.get("kind")
    ref = authorization.get("ref")
    if kind == SHADOW_KIND:
        return [
            "SHADOW detections never authorize a cure; detection is the "
            "beginning of adjudication, not a license to cure"
        ]
    if kind not in EVIDENCE_KINDS:
        return [
            f"cure-authorization kind {kind!r} is outside "
            f"{sorted(EVIDENCE_KINDS)}"
        ]
    if not isinstance(ref, str) or not EVIDENCE_KINDS[kind].fullmatch(ref):
        return [
            f"cure-authorization ref {ref!r} does not carry the {kind} form "
            f"{EVIDENCE_KINDS[kind].pattern}"
        ]
    if kind == OPERATOR_KIND:
        return operator_errors(authorization, tree, today or date.today())
    return []


def parse(value: str) -> dict[str, str]:
    """`kind=ref` from a command line into an authorization record.

    Provider-ref kinds are typeable. An operator adjudication is not, and that
    is deliberate: it needs a pinned subject and a resolvable artifact, so it
    arrives as a record in the proposal rather than as a sentence on a command
    line. A bare `operator-adjudication=...` from here is refused by
    `operator_errors` naming exactly what is missing.
    """
    kind, separator, ref = (value or "").partition("=")
    if not separator:
        raise ValueError(f"{DIAGNOSTIC}:cure-authorization must be <kind>=<ref>: {value!r}")
    return {"kind": kind.strip(), "ref": ref.strip()}


def refuse(
    subject: str,
    proposal_text: str,
    authorization: Any,
    *,
    always: bool = False,
    tree: Path | None = None,
    today: date | None = None,
) -> Refusal | None:
    """The single decision every BUILD carrier makes before it may write.

    `always=True` is for a carrier whose whole subject IS an enforcement shape -
    a catalogue class, a clause candidate - where scanning its text for the
    five shape words would only re-derive a fact already known from the verb.

    `tree` is what an operator adjudication's pinned subject resolves against.
    Every carrier has one and passes it; a carrier that does not is refused
    rather than silently graded on the weaker, shape-only reading.
    """
    shapes = shapes_in(proposal_text)
    if not shapes and not always:
        return None
    named = ",".join(shapes) if shapes else "the enforcement shape this verb carries"
    if authorization is None:
        return Refusal(
            DIAGNOSTIC,
            subject,
            f"introduces or alters {named} with no cure-authorization; {RULE}",
            ACTION,
        )
    errors = authorization_errors(authorization, tree=tree, today=today)
    if errors:
        # Every error, not the first: an operator record can be missing its
        # pinned subject AND its artifact at once, and a refusal that named one
        # of them would send the author back for a second round on one record.
        return Refusal(
            DIAGNOSTIC,
            subject,
            f"{'; '.join(errors)}; the shapes at stake are {named}",
            ACTION,
        )
    return None
