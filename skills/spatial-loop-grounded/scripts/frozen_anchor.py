#!/usr/bin/env python3
"""One rule for campaign receipts: a historical anchor freezes on first write.

A campaign receipt is a record of a run that already happened. Every field in
it that is *derived from the tree* -- the admitted tree sha the campaign
evaluated, the sha256 of the manual bytes the actors held -- is therefore a
historical fact, not a live view of whatever checkout the producer happens to
run in. Re-deriving one on a later regeneration rewrites the anchor to bytes no
actor ever held, and a producer does the writing, so the "never hand-edit a
campaign receipt" rule reads satisfied the whole time
(ed3c/skill-concerns#65 problem 1, ed3c/skill-concerns#104).

The cure is one shape, shared by every receipt producer here: the committed
receipt is an INPUT to its own producer, not only its output. `prior()` reads
it; `pin()` prefers what it already says. A genuinely new campaign writes to a
path with no prior, so `pin()` falls through to the freshly derived value
exactly once -- at the only moment that value is a fact about the run.

What this cannot do is notice that the first write was wrong. It freezes an
anchor; it does not verify one. That is a reader's job, and each producer's
anchor has a pinned expectation in
`skills/spatial-loop-grounded/tests/test_spatial_loop_grounded.py` -- because a
producer that echoes the committed value back cannot also vouch for it.
"""

from __future__ import annotations

import json
from pathlib import Path


def prior(path: Path) -> dict:
    """The receipt already committed at `path`; `{}` on a first write."""
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def pin(committed: dict, key: str, fresh: str) -> str:
    """`fresh` only while nothing is committed under `key`; then history wins."""
    return committed.get(key) or fresh
