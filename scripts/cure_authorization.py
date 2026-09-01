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
"""

from __future__ import annotations

import re
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
PROVIDER_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$")
OPERATOR_REF = re.compile(r"^operator:\d{4}-\d{2}-\d{2}:\S.*$")
EVIDENCE_KINDS: dict[str, re.Pattern[str]] = {
    "discriminating-measurement": PROVIDER_REF,
    "falsification": PROVIDER_REF,
    "operator-adjudication": OPERATOR_REF,
}
SHADOW_KIND = "shadow-detection"

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


def authorization_errors(authorization: Any) -> list[str]:
    """Everything wrong with an authorization record, or an empty list.

    Shape only. Whether the named issue's body really carries the measurement
    is the reviewer's read at landing time; what is mechanical here is that a
    proposal cannot proceed while pointing at nothing, at a SHADOW detection,
    or at a ref whose form contradicts the evidence it claims.
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
    return []


def parse(value: str) -> dict[str, str]:
    """`kind=ref` from a command line into an authorization record."""
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
) -> Refusal | None:
    """The single decision every BUILD carrier makes before it may write.

    `always=True` is for a carrier whose whole subject IS an enforcement shape -
    a catalogue class, a clause candidate - where scanning its text for the
    five shape words would only re-derive a fact already known from the verb.
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
    errors = authorization_errors(authorization)
    if errors:
        return Refusal(
            DIAGNOSTIC, subject, f"{errors[0]}; the shapes at stake are {named}", ACTION
        )
    return None
