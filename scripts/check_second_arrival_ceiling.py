#!/usr/bin/env python3
"""One ceiling for `userContentEdits.totalCount`, and every carrier states it.

`ed3c/skill-concerns#102` measured what the counter means, PROD-confirmed on
five issues across three waves: the connection materialises the ORIGINAL
revision as a node the moment any edit exists, so `0` is ABSENT rather than
NEGATIVE and the first edit moves the count `0 -> 2`. `#135` then found the
third carrier of that convention quoting a `totalCount` without any of it --
and observed that the two carriers which did state it agreed by coincidence of
authorship. Nothing read them together, so refining the arithmetic again would
have left all three untouched and none of them red.

The rule is therefore one sentence with one owner, and no list of carriers:

    a text file in this tree whose bytes mention `totalCount` carries
    `SECOND_ARRIVAL_CEILING` verbatim, or names that constant.

Two properties come out of that shape, and they are the two `#135` asked for.
Carriers are DISCOVERED, so a fourth one added tomorrow is covered on arrival
rather than needing a row here -- a per-carrier table inside a generic checker
would be the same defect one level up. And because the sentence is one string
with one owner, changing the arithmetic anywhere reds: edit a carrier's copy and
that carrier no longer matches the owner, edit the owner and every carrier that
quotes it reds at once. A fourth opinion cannot stand as a fourth opinion.

Naming the constant is the second way to satisfy the rule, for files that IMPORT
the sentence rather than quote it. A machine-carried ceiling cannot drift at
all, which is strictly stronger than a copied one, and a scan over bytes has no
other way to tell the two apart.

This is not a gate over the provider. It says nothing about whether any
particular count is right; it says that the documents in this tree which read
the counter read it the same way.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common import REPO_ROOT, print_result


# The counter this ceiling is about. A document that never names it is not a
# carrier -- naming the `userContentEdits` connection without ever quoting a
# count reads the surface, not the arithmetic.
COUNTER = "totalCount"

SECOND_ARRIVAL_CEILING = (
    "userContentEdits.totalCount counts the ORIGINAL revision: 0 is ABSENT, the first "
    "edit moves it 0 -> 2, and every later edit by one (ed3c/skill-concerns#102)"
)

OWNER_SYMBOL = "SECOND_ARRIVAL_CEILING"
DIAGNOSTIC = "SECOND_ARRIVAL_CEILING_ABSENT"

SKIP_DIRS = {".git", "__pycache__"}
# Text this repository authors. A binary or an unknown suffix is skipped rather
# than guessed at: a scan that decoded everything would report on bytes nobody
# writes by hand, and the carriers this rule is about are all authored text.
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".yml", ".yaml", ".diff", ".patch"}


def carriers(root: Path) -> list[Path]:
    """Every authored text file in `root` whose bytes read the counter."""
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or set(path.parts) & SKIP_DIRS:
            continue
        if path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if COUNTER in text:
            found.append(path)
    return found


def errors(root: Path) -> list[str]:
    """Which carriers state neither the ceiling nor the constant that owns it.

    This module is not exempted. It is the owner, so it carries the sentence by
    construction, and an exemption would be one line of the trust it is asking
    every other carrier for.
    """
    rows: list[str] = []
    for path in carriers(root):
        text = path.read_text(encoding="utf-8")
        if SECOND_ARRIVAL_CEILING in text or OWNER_SYMBOL in text:
            continue
        rows.append(
            f"{DIAGNOSTIC}:{path.relative_to(root).as_posix()}: reads {COUNTER!r} and "
            f"states neither the ceiling nor the constant that owns it. Carry "
            f"'{SECOND_ARRIVAL_CEILING}' verbatim, or name {OWNER_SYMBOL}"
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    return print_result("second-arrival-ceiling", errors(args.root.resolve()))


if __name__ == "__main__":
    raise SystemExit(main())
