#!/usr/bin/env python3
"""SHADOW: read one diff against the pinned precedent ledger and ask its questions.

Reader-only by construction, not by promise. The pass opens exactly the file it
was given, digests it before and after, and refuses its own report when the
digest moved (`SUBJECT_MUTATED`). Nothing here imports a way to spawn a process
or open a socket, which is the property one level under any list of forbidden
verbs: a module that cannot run a command cannot file, whatever strings it
happens to hold. `validate_shadow_architect.check_no_reach` is the reader for
that claim.

Signals are questions. A precedent match quotes the added bytes and asks the
clause's question; it never issues a verdict, and it never runs an experiment
against the subject. The falsification verb belongs to the sibling monitor that
owns it; the differential is deliberate and is written down in SKILL.md's
Non-claims.

Detection reads ADDED lines only, and acquittal reads added lines only too.
Unchanged context that merely mentions the right word does not exculpate a
shape the diff introduces - a detector whose acquittal ranges over context is
a detector any nearby comment can silence.

Acquittal is also scoped to the file whose bytes are being questioned, never
to the diff. An exculpation is a claim about one file's own added lines - this
path is normalised, this digest is pinned, this hazard is stated - and a
matcher that pooled them across the diff would let any one file's incantation,
including this bundle's own ledger travelling in the same landing, silence a
clause everywhere the diff reaches.

BUILD is `--fold-in`: one adjudicated precedent at a time, refused by the
repository's single cure-authorization implementation. A clause IS an
enforcement shape, so the refusal is unconditional rather than re-derived from
the candidate's wording.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import cure_authorization  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[1]

DIAGNOSTICS = (
    "PRECEDENT_WITHOUT_PROVENANCE",
    "PRECEDENT_FIXTURE_SILENT",
    "PRECEDENT_CONTROL_NOISY",
    "CLAUSE_WITHOUT_PRECEDENT",
    "PROVENANCE_RECORD_UNBOUND",
    "SUBJECT_MUTATED",
    "FINDING_MALFORMED",
    "DRIVER_SURFACE_FORBIDDEN",
    "ANSWER_KEY_VISIBLE",
    # Named by reference, never spelled: the diagnostic literal lives in exactly
    # one implementation, and a carrier that spelled it here would be a second
    # reading of the rule wearing the same name -- which is clause P3, applied
    # to this file.
    cure_authorization.DIAGNOSTIC,
)

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
NEW_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")

# The three severities, and each one has a producer rather than a field an
# author sets. S0 is a pass that asked nothing; S1 is one question; S2 is the
# same question in two or more files of one diff, because a shape repeated
# across files is architecture rather than an accident.
OBSERVE = "S0"
WARN = "S1"
REVIEW = "S2"


class BuildRefused(RuntimeError):
    """Raised instead of folding in a precedent nothing adjudicated."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def added_by_file(text: str) -> dict[str, list[tuple[int, str]]]:
    """path -> [(line number in the new file, added line)] for one unified diff.

    Line numbers are counted from each hunk's `+` start so a quoted byte can be
    pointed at, not merely pasted.
    """
    files: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    number = 0
    for raw in text.splitlines():
        header = NEW_FILE_RE.match(raw)
        if header:
            current = header.group(1)
            files.setdefault(current, [])
            continue
        hunk = HUNK_RE.match(raw)
        if hunk:
            number = int(hunk.group(1))
            continue
        if current is None:
            continue
        if raw.startswith("+"):
            files[current].append((number, raw[1:]))
            number += 1
        elif not raw.startswith("-"):
            number += 1
    return files


def _unread_fields(files: dict[str, list[tuple[int, str]]]) -> dict[str, list[tuple[int, str]]]:
    """Fields a diff ADDS to data and mentions in code only inside refusals."""
    data_keys = {
        match.group("field")
        for path, lines in files.items()
        if not path.endswith(".py")
        for _, line in lines
        for match in [DATA_KEY_RE.match(line)]
        if match
    }
    found: dict[str, list[tuple[int, str]]] = {}
    for path, lines in files.items():
        if not path.endswith(".py"):
            continue
        read = {
            match.group("field")
            for _, line in lines
            for match in GET_RE.finditer(line)
        }
        for field in sorted(read & data_keys):
            mentions = [(number, line) for number, line in lines if field in line]
            if mentions and all(REFUSAL_RE.search(line) for _, line in mentions):
                found.setdefault(path, []).append(mentions[0])
    return found


DATA_KEY_RE = re.compile(r"""^\s*["'](?P<field>[A-Za-z_]\w*)["']\s*:""")
GET_RE = re.compile(r"""\.get\(\s*["'](?P<field>[A-Za-z_]\w*)["']""")
REFUSAL_RE = re.compile(r"(?:if not\b|errors\.append|raise |assert |fullmatch)")


def acquitted(lines: list[tuple[int, str]], patterns: list[str]) -> bool:
    """Does this ONE file's own added text carry its own exculpation?"""
    added = "\n".join(line for _, line in lines)
    return any(re.search(pattern, added) for pattern in patterns)


def match(precedent: dict, text: str) -> list[tuple[str, int, str]]:
    """(path, line, added bytes) for every place this precedent asks its question."""
    files = added_by_file(text)
    scope = precedent.get("paths")
    patterns = precedent.get("acquittal") or []
    scoped = {
        path: lines
        for path, lines in files.items()
        if (not scope or re.search(scope, path)) and not acquitted(lines, patterns)
    }
    if precedent.get("kind") == "unread-field":
        return [
            (path, number, line)
            for path, mentions in _unread_fields(scoped).items()
            for number, line in mentions
        ]
    return [
        (path, number, line)
        for path, lines in scoped.items()
        for number, line in lines
        if any(re.search(pattern, line) for pattern in precedent.get("signal") or [])
    ]


def finding(precedent: dict, subject: dict, hits: list[tuple[str, int, str]]) -> dict:
    provenance = precedent.get("provenance") or {}
    return {
        "clause": precedent["id"],
        "severity": REVIEW if len({path for path, _, _ in hits}) > 1 else WARN,
        "question": precedent.get("question", ""),
        "subject": subject,
        "quoted": [
            {"path": path, "line": number, "bytes": line.strip()}
            for path, number, line in hits
        ],
        "precedent": {
            "wave": provenance.get("wave"),
            "monitor_record": provenance.get("monitor_record"),
            "wave_receipt": provenance.get("wave_receipt"),
        },
    }


def finding_errors(record: Any) -> list[str]:
    """Everything wrong with one finding, or an empty list.

    Declared once, here, and imported by every reader that judges a record --
    including the validator, which calls this rather than restating it. A
    second copy phrased as ownership would be two readings of one schema
    wearing one name, which is clause P3 applied to this bundle.
    """
    if not isinstance(record, dict):
        return [f"finding is not a record: {record!r}"]
    errors = [
        f"missing field {field!r}"
        for field in ("clause", "severity", "question", "subject", "quoted", "precedent")
        if field not in record
    ]
    if errors:
        return errors
    if record["severity"] not in (WARN, REVIEW):
        errors.append(f"severity {record['severity']!r} is outside {[WARN, REVIEW]}")
    subject = record["subject"]
    if not isinstance(subject, dict) or not subject.get("path"):
        errors.append("subject names no path")
    elif not re.fullmatch(r"[0-9a-f]{64}", str(subject.get("sha256", ""))):
        errors.append(f"subject {subject['path']} is not bound to an exact sha256")
    quoted = record["quoted"]
    if not isinstance(quoted, list) or not quoted:
        errors.append("a signal with no quoted bytes is an opinion")
    else:
        for item in quoted:
            if not isinstance(item, dict) or not str(item.get("bytes") or "").strip():
                errors.append(f"quoted entry carries no bytes: {item!r}")
            elif not isinstance(item.get("line"), int):
                errors.append(f"quoted {item.get('path')!r} names no line")
    if not str(record["question"] or "").strip():
        errors.append("a finding with no question is a verdict this bundle may not issue")
    precedent = record["precedent"]
    if not isinstance(precedent, dict) or not precedent.get("wave_receipt"):
        errors.append("finding cites no wave receipt")
    return errors


def run(diff_path: Path, ledger: dict) -> dict:
    """One reader-only pass over one diff."""
    before = digest(diff_path)
    text = diff_path.read_text(encoding="utf-8", errors="replace")
    findings = []
    for precedent in ledger.get("precedents") or []:
        hits = match(precedent, text)
        if hits:
            findings.append(finding(precedent, {"path": diff_path.name, "sha256": before}, hits))
    after = digest(diff_path)
    report = {
        "schema_version": 1,
        "mode": "shadow",
        "subject": {"path": diff_path.name, "sha256": before},
        "precedents_read": len(ledger.get("precedents") or []),
        "findings": findings,
        "read_only": {"digest_before": before, "digest_after": after, "held": before == after},
    }
    if not report["read_only"]["held"]:
        report["findings"] = []
        report["outcome"] = "blocked"
        report["refusal"] = (
            f"SUBJECT_MUTATED:{diff_path.name}: a reader-only pass has no write verb, yet "
            f"the subject digest moved {before} -> {after}; this report is untrusted"
        )
        return report
    malformed = [error for record in findings for error in finding_errors(record)]
    if malformed:
        report["findings"] = []
        report["outcome"] = "blocked"
        report["refusal"] = f"FINDING_MALFORMED:{diff_path.name}: {malformed[0]}"
        return report
    report["outcome"] = "changed" if findings else "clean"
    report["severity"] = (
        max((record["severity"] for record in findings), default=OBSERVE)
    )
    return report


def render_findings(report: dict) -> str:
    """The numbered findings block a dispatcher pastes into an issue body.

    No fenced block: the consumer's admission gate strips fences before it
    decides whether a section carries an authored assertion, so a fenced block
    arrives there empty.
    """
    if not report["findings"]:
        return f"{OBSERVE} no findings: {report['subject']['path']} raised no pinned precedent."
    lines = []
    for number, record in enumerate(report["findings"], start=1):
        quoted = record["quoted"][0]
        lines.append(
            f"{number}. [{record['severity']}] {record['clause']} - {record['question']}"
        )
        lines.append(f"   subject: {record['subject']['path']}@{record['subject']['sha256']}")
        lines.append(f"   quoted: {quoted['path']}:{quoted['line']}: {quoted['bytes']}")
        lines.append(
            "   precedent: "
            f"{record['precedent']['monitor_record']} "
            f"({', '.join(record['precedent']['wave_receipt'])})"
        )
    return "\n".join(lines)


def fold_in(ledger: dict, candidate: Any) -> dict:
    """BUILD: return the ledger with `candidate` appended, or refuse.

    A precedent clause IS an enforcement shape - it is the thing a monitor
    judges against - so the cure-authorization refusal is unconditional rather
    than re-derived from the candidate's wording, which would only rediscover a
    fact already known from the verb. The decision itself lives once, in the
    repository's shared implementation, and is called here rather than restated.
    """
    if not isinstance(candidate, dict) or not candidate.get("id"):
        raise BuildRefused("PRECEDENT_WITHOUT_PROVENANCE:<unidentified>:candidate has no id")
    clause = candidate["id"]
    if any(entry.get("id") == clause for entry in ledger.get("precedents") or []):
        raise BuildRefused(f"PRECEDENT_WITHOUT_PROVENANCE:{clause}:already in the ledger")
    refusal = cure_authorization.refuse(
        clause,
        json.dumps({k: v for k, v in candidate.items() if k != "cure_authorization"}),
        candidate.get("cure_authorization"),
        always=True,
    )
    if refusal is not None:
        raise BuildRefused(str(refusal))
    provenance = candidate.get("provenance") or {}
    if not provenance.get("wave_receipt") or not str(provenance.get("quote") or "").strip():
        raise BuildRefused(
            f"PRECEDENT_WITHOUT_PROVENANCE:{clause}:no wave receipt and no monitor quote, "
            "so nothing says which wave found this"
        )
    folded = dict(ledger)
    folded["precedents"] = [*(ledger.get("precedents") or []), candidate]
    return folded


def load_ledger(skill_root: Path = SKILL_ROOT) -> dict:
    return json.loads(
        (skill_root / "domain" / "precedents.json").read_text(encoding="utf-8")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--diff", type=Path, help="the unified diff to read")
    parser.add_argument("--skill-root", type=Path, default=SKILL_ROOT)
    parser.add_argument("--clause", help="report only this precedent")
    parser.add_argument("--render", action="store_true", help="emit the issue-body block")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.diff is None:
        build_parser().print_help()
        return 2
    ledger = load_ledger(args.skill_root.resolve())
    if args.clause:
        ledger = {
            **ledger,
            "precedents": [
                entry
                for entry in ledger.get("precedents") or []
                if entry.get("id") == args.clause
            ],
        }
    report = run(args.diff.resolve(), ledger)
    print(render_findings(report) if args.render else json.dumps(report, indent=2))
    return 1 if report["outcome"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
