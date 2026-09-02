#!/usr/bin/env python3
"""Cadence sweep over admitted Skill content freshness.

Index freshness has an owner (launchd + canary); Skill CONTENT freshness had
none. Admitted Skills carry receipts pinned to commits, paths, digests and
upstream facts that drift silently while nothing re-reads them. This sweep is
that missing owner.

Loop shape is adopted from the pinned pstack donor
(cursor/plugins@b9ddc83c32972210b8a94d389130713e8eed346e,
`pstack/skills/maintain-verification-skill/SKILL.md`):

  three outcomes  clean / changed / blocked, always named, never merged;
  edit scope      the run may not modify the subject; the guard is a digest
                  taken before and after the pass, not a promise;
  live-pass       doctor before drive; evidence survives cleanup and is
  invariants      checked at its named location; no residue outlives the run.

The subject here is admitted-Skill receipts and selftests rather than an app
feature map, so "drive" means: re-run each Skill's own declared checks
(`run_all.SKILL_CHECKS`, i.e. its validator plus the executable selftests those
validators shell out to) and the repository gates that recompute every pinned
path and digest, then re-check the pins no gate can see - receipt refs that
must still resolve at the provider, and `policy/upstream-pins.json`.

N-class: this sweep gates nothing. No admission, stamp, or CI path reads its
exit code or its report (`tests/test_maintain_skills.py::test_sweep_gates_nothing`
is the mechanical reader for that claim). Drift leaves SHADOW as a finding with
a destination, never as a patch.

Two modes, and the split is the point (ed3c/skill-concerns#62)
--------------------------------------------------------------

SHADOW is the default and has no write verb at all: `sweep()` reads, reports,
and proves it stayed a reader by digesting EDIT_SCOPE before and after the
pass. A pass that finds the digest moved refuses its own report
(`EDIT_SCOPE_VIOLATION`, outcome `blocked`) rather than publishing findings
derived from a tree something mutated underneath it - the planted check that
writes into `skills/` in `selftest()` is the negative control for that.

BUILD is `--pass SKILL` and is the only half allowed to propose bytes. It may
not apply them anywhere a reader would mistake for a landing:

  branch          it creates `maintain/<skill>-<stamp>` and returns the
                  checkout to the base branch before it exits; the base head
                  sha is read before and after and must be unchanged.
  edit scope      writes may land only under `skills/<skill>/` within this
                  checkout. The guard is `git status --porcelain -uall`
                  after every producer, not a promise: one out-of-scope path
                  git can see refuses the whole producer, restores the tree,
                  and blocks the pass. A producer that writes to an absolute
                  path outside this checkout entirely is outside what a
                  git-status diff can see - a known gap, not covered by this
                  guard (filed: ed3c/skill-concerns#66).
  producers       corrections regenerate through the subject Skill's own
                  `scripts/gen_*.py`, never by hand (spatial-loop-grounded C5).
                  `REPOSITORY_PRODUCERS` are excluded because their output is a
                  repository artifact (`admissions/`, `intake/`) by contract,
                  not the Skill's own directory.
  adjudicated     a proposal whose added lines introduce or alter an
                  enforcement shape (gate, ratchet, threshold, refusal,
                  escape-hatch) must name a cure-authorization, or it is
                  refused with `BUILD_CURE_UNAUTHORIZED`. The decision is
                  `cure_authorization.refuse()` and lives there once; this
                  carrier and `skills/arrival-engineering`'s topology append
                  call the same function rather than each reading the rule
                  (ed3c/skill-concerns#93).
  proven          the subject's own `run_all.SKILL_CHECKS` row runs against
                  the proposal before it becomes a commit; a red row blocks
                  the pass rather than shipping bytes nobody re-ran. A skill
                  with no row at all is blocked too (`BUILD_SKILL_UNCHECKED`)
                  rather than reading as vacuously proven. That row and no
                  more: `check_admissions.py` reds by construction here (the
                  receipt pins the bytes BUILD just moved) and the re-stamp
                  is a landing act, not a proposing one.
  three outcomes  clean (nothing to propose), changed (a proven proposal sits
                  on the branch), blocked (a refusal; nothing ships).

Adjudications carried as bytes (ed3c/skill-concerns#59) - AGENTS.md is the source
----------------------------------------------------------------------------------

The runtime/ceremony boundary, filing-not-reflex coupling, and trigger-not-
apply exception rulings live in AGENTS.md ("Adjudications carried here as
bytes"), not here. AGENTS.md's own rule for this kind of split is "POINT at
it, never restate it; a restated copy is the drift the split exists to
prevent" - this module obeys that rule about itself: this pass's behavior
(no auto-invoke, no auto-apply, filed findings) is the enforcement of those
three rulings, not a second copy of their prose.
tests/test_maintain_skills.py::test_maintain_docs_carry_the_sc59_adjudications
is the mechanical reader, and it reads AGENTS.md.

Re-running `run_all.SKILL_CHECKS` and the repository gates duplicates argv CI
already runs on every commit - by design, that half is a pure function of
tree bytes and cannot disagree with CI on the same commit. Its incremental
value is the two things CI cannot see: local drift in a working tree that
was never committed (this sweep runs against `--root`, a live filesystem
path, not a merged ref - `git["dirty"]` in the report says whether that
matters for this run), and interpreter/environment bit-rot between the last
CI run and today. Whether that value justifies re-deriving 15 rows nightly
rather than shipping only the two provider-pin checks below is an open
sizing question, not settled here - filed at this paragraph
(scripts/maintain_skills.py, this docstring) for a future pass to revisit
once `git["dirty"]` has produced evidence either way.

Exit codes: 0 clean, 1 changed (drift found), 2 blocked (coverage unfinished).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cure_authorization  # noqa: E402
from common import (  # noqa: E402
    REPO_ROOT,
    compare_digest_entries,
    digest_entries,
    regular_files,
    tree_digest,
)
import run_all  # noqa: E402


REPO_GATES = ("check_agents_hops.py", "check_skill_bundles.py", "check_admissions.py")

# Everything the sweep reads as subject and must leave byte-identical.
EDIT_SCOPE = ("skills", "admissions", "intake", "contracts", "policy", "registry.json")

# BUILD refuses to run these: they write repository artifacts (`admissions/`,
# `intake/`) by contract, so every run would be an edit-scope refusal, and
# gen_admission re-executes the whole Skill suite before it writes.
REPOSITORY_PRODUCERS = ("gen_admission.py", "gen_source_lock.py")

# The identity on a proposal commit. BUILD proposes; a human lands. Inline so
# the pass never depends on - or inherits - the operator's git config.
BUILD_IDENTITY = ("-c", "user.name=maintain-skills", "-c", "user.email=maintain-skills@invalid")

# Files that hold pins, searched in order to give every finding a path:line
# destination that exists in this tree.
PIN_HOLDER_GLOBS = (
    "policy/upstream-pins.json",
    "skills/*/receipts.json",
    "intake/*/source-lock.json",
    "admissions/*.json",
    "registry.json",
)

PROVIDER_REF = re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(?P<number>\d+)$")
GATE_ERROR = re.compile(r"^(?P<diagnostic>[A-Z][A-Z0-9_]*):(?P<subject>.+)$")


# --------------------------------------------------------------------------
# subject integrity


def scope_entries(root: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for relative in EDIT_SCOPE:
        path = root / relative
        if path.is_dir():
            entries.extend(digest_entries(root, regular_files(path)))
        elif path.is_file():
            entries.extend(digest_entries(root, [path]))
    return entries


def scope_digest(root: Path) -> str:
    return tree_digest(scope_entries(root))


def locate_destination(root: Path, subject: str) -> str:
    """A finding is filed at the line of the pin that carries it.

    Only a subject specific enough to be a real pin value (never a bare
    argv flag like "-m") is worth searching for; short/generic subjects
    return the explicit sentinel below instead of an accidental substring
    hit on an unrelated file.
    """
    if len(subject) >= 4:
        for pattern in PIN_HOLDER_GLOBS:
            for path in sorted(root.glob(pattern)):
                if not path.is_file():
                    continue
                for number, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), start=1
                ):
                    if subject in line:
                        return f"{path.relative_to(root).as_posix()}:{number}"
    # No pin file names this subject. Never guess: a made-up path:line
    # that happens to exist (e.g. registry.json:1) is worse than an
    # explicit "not found" because it silently misdirects a reader.
    return f"NO_MATCHING_PIN:{subject}"


def finding(
    root: Path, diagnostic: str, subject: str, detail: str, action: str
) -> dict[str, str]:
    return {
        "diagnostic": diagnostic,
        "subject": subject,
        "detail": detail,
        "destination": locate_destination(root, subject),
        "action": action,
    }


# --------------------------------------------------------------------------
# doctor - run before any drive, never after a surprise


def doctor(root: Path, online: bool) -> list[str]:
    blockers: list[str] = []
    for required in ("registry.json", "scripts/run_all.py", "policy/upstream-pins.json"):
        if not (root / required).is_file():
            blockers.append(f"DOCTOR_SUBJECT_INCOMPLETE:{required}")
    if online:
        probe = _run(["gh", "api", "rate_limit", "--jq", ".rate.remaining"], root)
        if probe["returncode"] != 0:
            blockers.append(f"DOCTOR_PROVIDER_UNREACHABLE:{probe['tail']}")
    return blockers


def git_identity(root: Path) -> dict[str, Any]:
    """Best-effort git identity of the tree the pass ran against.

    Non-fatal by design: the selftest drives sweep() against a scratch copy
    with no .git (see selftest()), and that must stay clean, not blocked.
    A null field here means "not a git checkout", not "unknown drift".
    """
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root, timeout=10)
    head = _run(["git", "rev-parse", "HEAD"], root, timeout=10)
    status = _run(["git", "status", "--porcelain"], root, timeout=10)
    return {
        "branch": branch["stdout"].strip() if branch["returncode"] == 0 else None,
        "head": head["stdout"].strip() if head["returncode"] == 0 else None,
        "dirty": bool(status["stdout"].strip()) if status["returncode"] == 0 else None,
    }


def _run(command: list[str], cwd: Path, timeout: int = 900) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        return {"returncode": 127, "stdout": "", "tail": f"{exc}"}
    except subprocess.TimeoutExpired:
        return {"returncode": 124, "stdout": "", "tail": f"timeout after {timeout}s"}
    tail = (completed.stdout + completed.stderr).strip().splitlines()
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "tail": " | ".join(tail[-3:]),
    }


# --------------------------------------------------------------------------
# drive: the tree's own checks


def check_rows(root: Path, run_skill_checks: bool) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = [
        (f"repository:{gate}", [f"scripts/{gate}", "--root", str(root)])
        for gate in REPO_GATES
    ]
    if run_skill_checks:
        for skill, checks in run_all.SKILL_CHECKS.items():
            for argv in checks:
                rows.append((f"skill:{skill}", list(argv)))
    return rows


def drive_checks(
    root: Path, rows: Iterable[tuple[str, list[str]]]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    results: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    for subject, argv in rows:
        outcome = _run([sys.executable, *argv], root)
        state = "PASS" if outcome["returncode"] == 0 else "FAIL"
        results.append(
            {
                "subject": subject,
                "argv": argv,
                "state": state,
                "tail": outcome["tail"] if state == "FAIL" else "",
            }
        )
        if state == "FAIL":
            findings.extend(_gate_findings(root, subject, argv, outcome))
    return results, findings


def _gate_findings(
    root: Path, subject: str, argv: list[str], outcome: dict[str, Any]
) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for line in outcome["stdout"].splitlines():
        match = GATE_ERROR.match(line.strip())
        if match:
            found.append(
                finding(
                    root,
                    match.group("diagnostic"),
                    match.group("subject"),
                    f"{subject} reported it",
                    "regenerate the pin through its producer, or correct the subject; never edit the pin to match drifted bytes",
                )
            )
    if not found:
        found.append(_check_failed_finding(root, subject, argv, outcome))
    return found


def _check_failed_finding(
    root: Path, subject: str, argv: list[str], outcome: dict[str, Any]
) -> dict[str, str]:
    """CHECK_FAILED with no machine-readable diagnostic line in its output.

    argv[0] alone is a bad destination key: for the `-m unittest discover`
    rows it is the literal string "-m", which locate_destination's old
    substring search could match against any short fragment in any pin
    file. Bind to the first argv element that is a real path in this tree
    and is neither a flag nor the root itself (the discover target
    directory for those rows, the script path otherwise) - a destination
    that is correct by construction, never by accidental substring
    collision, and never a directory-flag value like `--root .`.
    """
    candidates = [a for a in argv if not a.startswith("-") and a not in (".", str(root))]
    candidate = next((a for a in candidates if (root / a).is_file() or (root / a).is_dir()), None)
    destination = f"{candidate}:1" if candidate else f"NO_MATCHING_PIN:{argv[0]}"
    return {
        "diagnostic": "CHECK_FAILED",
        "subject": argv[0],
        "detail": f"{subject}: {outcome['tail']}",
        "destination": destination,
        "action": "re-run this check by hand and read its output",
    }


# --------------------------------------------------------------------------
# drive: pins no gate can see


def receipt_refs(root: Path) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for path in sorted(root.glob("skills/*/receipts.json")):
        skill = path.parent.name
        evidence = json.loads(path.read_text(encoding="utf-8")).get("evidence", {})
        for entry in evidence.values():
            for ref in entry.get("refs") or []:
                if isinstance(ref, str) and (skill, ref) not in refs:
                    refs.append((skill, ref))
    return refs


def ref_state(returncode: int, tail: str) -> str:
    """Classify one provider read. Absence and unreadability never look alike."""
    if returncode == 0:
        return "RESOLVED"
    if "HTTP 404" in tail or "Not Found" in tail:
        return "UNRESOLVED"
    return "BLOCKED"


def ancestry_ok(status: str) -> bool:
    """compare(base=pin, head=branch): the pin is reachable from the branch."""
    return status in {"identical", "ahead"}


def mirror_destination(root: Path, mirror: Any) -> str | None:
    """`path:line` of the local copy whose shape a watched upstream file sets.

    Without this a watched-file finding is filed at the pin that noticed it,
    which is the one file the reader does not have to change: the pin is
    correct, the MIRROR is what has to be re-derived. The line is resolved by
    searching for the declared anchor rather than recorded as a number, so the
    destination does not go stale the first time the mirror is edited.

    A mirror that is not there, or an anchor the mirror no longer carries, gets
    its own sentinel rather than a plausible-looking `path:1` -- the same rule
    `locate_destination` follows about never guessing a destination.
    """
    if not isinstance(mirror, dict):
        return None
    relative = str(mirror.get("path", ""))
    anchor = str(mirror.get("anchor", ""))
    if not relative or not anchor:
        return f"MIRROR_DECLARATION_INCOMPLETE:{relative or anchor}"
    path = root / relative
    if not path.is_file():
        return f"MIRROR_ABSENT:{relative}"
    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if anchor in line:
            return f"{relative}:{number}"
    return f"MIRROR_ANCHOR_ABSENT:{relative}:{anchor}"


def check_refs(
    root: Path, online: bool
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Resolve every receipt ref read-only. Never issues a write verb."""
    results: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []
    unreachable: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for skill, ref in receipt_refs(root):
        match = PROVIDER_REF.match(ref)
        if not match:
            unreachable.append(
                {
                    "pin": ref,
                    "skill": skill,
                    "prerequisite": "a host artifact this sweep cannot observe (log file, launchctl label)",
                    "destination": locate_destination(root, ref),
                }
            )
            continue
        if not online:
            unreachable.append(
                {
                    "pin": ref,
                    "skill": skill,
                    "prerequisite": "network + gh auth (run without --offline)",
                    "destination": locate_destination(root, ref),
                }
            )
            continue
        if ref not in seen:
            repository, number = match.group("repo"), match.group("number")
            probe = _run(
                [
                    "gh",
                    "api",
                    f"repos/{repository}/issues/{number}",
                    "--jq",
                    ".number",
                ],
                root,
                timeout=60,
            )
            seen[ref] = ref_state(probe["returncode"], probe["tail"])
            if seen[ref] == "BLOCKED":
                unreachable.append(
                    {
                        "pin": ref,
                        "skill": skill,
                        "prerequisite": f"provider readable: {probe['tail']}",
                        "destination": locate_destination(root, ref),
                    }
                )
        state = seen[ref]
        results.append({"pin": ref, "skill": skill, "state": state})
        if state == "UNRESOLVED":
            findings.append(
                finding(
                    root,
                    "RECEIPT_REF_UNRESOLVED",
                    ref,
                    f"{skill} cites {ref}; the provider does not serve it",
                    "re-anchor the receipt on a ref that resolves, or record the claim as host-held evidence",
                )
            )
    return results, findings, unreachable


def check_upstream(
    root: Path, online: bool
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    results: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []
    unreachable: list[dict[str, str]] = []
    document = json.loads((root / "policy" / "upstream-pins.json").read_text(encoding="utf-8"))
    for pin in document.get("pins", []):
        repository = pin["repository"]
        branch = pin.get("branch", "main")
        # A pin may watch FILE identity without pinning a commit
        # (ed3c/skill-concerns#97). A consumer repository's head moves every
        # day and reporting that as drift would leave the cadence permanently
        # `changed` over a fact nobody watches, drowning the findings that
        # matter. The field's presence is the switch, so there is no second
        # flag to keep in step with it.
        commit = pin.get("pinned_commit")
        anchor = commit or pin["id"]
        if not online:
            unreachable.append(
                {
                    "pin": pin["id"],
                    "skill": repository,
                    "prerequisite": "network + gh auth (run without --offline)",
                    "destination": locate_destination(root, anchor),
                }
            )
            continue

        if commit:
            head = _run(
                ["gh", "api", f"repos/{repository}/commits/{branch}", "--jq", ".sha"], root, 60
            )
            if head["returncode"] != 0:
                unreachable.append(
                    {
                        "pin": pin["id"],
                        "skill": repository,
                        "prerequisite": f"provider readable: {head['tail']}",
                        "destination": locate_destination(root, anchor),
                    }
                )
                # Mirror check_refs: a genuine online read failure is not the
                # same as "skipped by --offline" and must degrade the outcome,
                # or the entire upstream-pin subject silently disappears behind
                # a "clean" report.
                results.append({"pin": f"{pin['id']}:head", "skill": repository, "state": "BLOCKED"})
                continue
            head_sha = head["stdout"].strip()
            results.append({"pin": f"{pin['id']}:head", "skill": repository, "state": head_sha})
            if head_sha != commit:
                findings.append(
                    finding(
                        root,
                        "UPSTREAM_MAIN_MOVED",
                        commit,
                        f"{repository} {branch} is at {head_sha}; the pin names {commit}",
                        pin.get("action_on_drift", "re-read the pinned upstream files"),
                    )
                )

            # The ancestry fact: a moved head is routine, an unreachable pin is not.
            compare = _run(
                [
                    "gh",
                    "api",
                    f"repos/{repository}/compare/{commit}...{branch}",
                    "--jq",
                    ".status",
                ],
                root,
                60,
            )
            if compare["returncode"] != 0:
                unreachable.append(
                    {
                        "pin": f"{pin['id']}:ancestry",
                        "skill": repository,
                        "prerequisite": f"provider readable: {compare['tail']}",
                        "destination": locate_destination(root, anchor),
                    }
                )
                results.append(
                    {"pin": f"{pin['id']}:ancestry", "skill": repository, "state": "BLOCKED"}
                )
            else:
                status = compare["stdout"].strip()
                results.append(
                    {"pin": f"{pin['id']}:ancestry", "skill": repository, "state": status}
                )
                if not ancestry_ok(status):
                    findings.append(
                        finding(
                            root,
                            "UPSTREAM_PIN_NOT_ANCESTOR",
                            commit,
                            f"compare {commit}...{branch} is {status!r}; the pinned commit is no longer reachable from {branch}",
                            "stop citing this pstack commit until the pin is re-anchored on a commit that is an ancestor of "
                            f"{repository} {branch}",
                        )
                    )

        for watched in pin.get("watched_files", []):
            destination = mirror_destination(root, watched.get("mirror"))
            blob = _run(
                [
                    "gh",
                    "api",
                    f"repos/{repository}/contents/{watched['path']}?ref={branch}",
                    "--jq",
                    ".sha",
                ],
                root,
                60,
            )
            if blob["returncode"] != 0:
                unreachable.append(
                    {
                        "pin": watched["path"],
                        "skill": repository,
                        "prerequisite": f"provider readable: {blob['tail']}",
                        "destination": destination
                        or locate_destination(root, watched["blob_sha"]),
                    }
                )
                results.append({"pin": watched["path"], "skill": repository, "state": "BLOCKED"})
                continue
            current = blob["stdout"].strip()
            results.append(
                {"pin": watched["path"], "skill": repository, "state": current}
            )
            if current != watched["blob_sha"]:
                drift = finding(
                    root,
                    "UPSTREAM_WATCHED_FILE_CHANGED",
                    watched["blob_sha"],
                    f"{repository}:{watched['path']} is blob {current}; the pin names {watched['blob_sha']}",
                    pin.get("action_on_drift", "re-read the pinned upstream file"),
                )
                if destination:
                    drift["destination"] = destination
                findings.append(drift)
    return results, findings, unreachable


# --------------------------------------------------------------------------
# the pass


def sweep(root: Path, *, run_skill_checks: bool = True, online: bool = True) -> dict[str, Any]:
    root = root.resolve()
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root),
        "git": git_identity(root),
        "mode": "shadow",
        "outcome": "blocked",
        "online": online,
        "skill_checks_run": run_skill_checks,
        "doctor": [],
        "edit_scope": {},
        "checks": [],
        "pins": [],
        "findings": [],
        "unreachable": [],
        "filing_route": (
            "each finding is filed at its destination path:line in this tree; "
            "nothing in this file escalates a finding into a GitHub issue - "
            "that promotion, if wanted, is a human or a future reader's job"
        ),
    }

    blockers = doctor(root, online)
    report["doctor"] = blockers
    if blockers:
        return report

    entries_before = scope_entries(root)
    before = tree_digest(entries_before)
    checks, check_findings = drive_checks(root, check_rows(root, run_skill_checks))
    ref_pins, ref_findings, ref_unreachable = check_refs(root, online)
    upstream_pins, upstream_findings, upstream_unreachable = check_upstream(root, online)
    entries_after = scope_entries(root)
    after = tree_digest(entries_after)

    report["checks"] = checks
    report["pins"] = ref_pins + upstream_pins
    report["findings"] = check_findings + ref_findings + upstream_findings
    report["unreachable"] = ref_unreachable + upstream_unreachable
    # Name the paths, not just the digests: "registry.json" used to be the
    # hardcoded subject of this finding, which sent every reader to a file
    # that was usually innocent. compare_digest_entries names what moved.
    moved = compare_digest_entries(entries_after, entries_before, "SHADOW_SCOPE")
    report["edit_scope"] = {
        "digest_before": before,
        "digest_after": after,
        "held": before == after,
        "moved": moved,
    }

    if not report["edit_scope"]["held"]:
        report["findings"].insert(
            0,
            finding(
                root,
                "EDIT_SCOPE_VIOLATION",
                moved[0].split(":", 1)[1] if moved else "registry.json",
                f"a SHADOW pass has no write verb, yet the subject digest moved "
                f"{before} -> {after}: {', '.join(moved) or 'unattributable'}",
                "the sweep must not write to the subject; treat this run's report as untrusted",
            ),
        )
        report["outcome"] = "blocked"
    elif any(item["state"] == "BLOCKED" for item in report["pins"]):
        report["outcome"] = "blocked"
    elif report["findings"]:
        report["outcome"] = "changed"
    else:
        report["outcome"] = "clean"
    return report


# --------------------------------------------------------------------------
# BUILD: the only half with a write verb, and it may only propose


def _git(root: Path, *args: str, identity: bool = False) -> dict[str, Any]:
    prefix = list(BUILD_IDENTITY) if identity else []
    return _run(["git", *prefix, *args], root, timeout=120)


def worktree_changes(root: Path) -> list[str]:
    """Every path git sees as changed, tracked or not.

    The guard is git rather than a digest over EDIT_SCOPE because BUILD's
    refusal has to cover paths EDIT_SCOPE never listed - a producer that
    writes `scripts/`, `.github/`, or a brand new top-level file is exactly
    the escape the guard exists to catch, and a hand-listed scope tuple
    cannot see one it was never told about.
    """
    status = _git(root, "status", "--porcelain", "--untracked-files=all")
    if status["returncode"] != 0:
        raise SystemExit(f"BUILD_STATUS_UNREADABLE:{status['tail']}")
    paths: list[str] = []
    for line in status["stdout"].splitlines():
        entry = line[3:].strip()
        if " -> " in entry:  # a rename reports old -> new
            entry = entry.split(" -> ", 1)[1]
        paths.append(entry.strip('"'))
    return sorted(paths)


def build_producers(root: Path, skill: str) -> list[str]:
    """The subject Skill's own regeneration producers, repository ones removed."""
    directory = root / "skills" / skill / "scripts"
    if not directory.is_dir():
        return []
    return [
        path.relative_to(root).as_posix()
        for path in sorted(directory.glob("gen_*.py"))
        if path.name not in REPOSITORY_PRODUCERS
    ]


def build_doctor(root: Path, skill: str) -> list[str]:
    blockers: list[str] = []
    if not (root / "skills" / skill).is_dir():
        blockers.append(f"DOCTOR_SUBJECT_ABSENT:skills/{skill}")
    if _git(root, "rev-parse", "--git-dir")["returncode"] != 0:
        blockers.append("DOCTOR_NOT_A_CHECKOUT:BUILD proposes on a branch it creates")
        return blockers
    dirty = worktree_changes(root)
    if dirty:
        # Refusing here is what makes the guard readable at all: a pass that
        # starts dirty cannot tell its own writes from the operator's.
        blockers.append(f"DOCTOR_WORKTREE_DIRTY:{','.join(dirty[:5])}")
    return blockers


def restore(root: Path) -> list[str]:
    """Undo everything a refused producer wrote. Returns what is still dirty."""
    _git(root, "checkout", "--", ".")
    # Whatever survives the checkout is untracked - producer output git has no
    # committed byte to restore. Remove exactly those, then re-read the tree:
    # the return value is a measurement, not the claim that it worked.
    for relative in worktree_changes(root):
        path = root / relative
        if path.is_file():
            path.unlink()
    return worktree_changes(root)


def proposal_additions(root: Path, scope: str) -> str:
    """Every line the proposal ADDS under `scope`, tracked and untracked alike.

    Added lines only: a producer that rewrites a file leaves the unchanged
    context lines in the diff, and scanning those would make an existing gate's
    own vocabulary read as a gate the proposal introduced. `--unified=0` drops
    the context; the untracked half has no committed side, so its whole text is
    the addition.
    """
    diff = _git(root, "diff", "--unified=0", "--", scope)
    added = [
        line[1:]
        for line in diff["stdout"].splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    new_files = _git(root, "ls-files", "--others", "--exclude-standard", "--", scope)
    for relative in new_files["stdout"].splitlines():
        path = root / relative.strip()
        if path.is_file():
            try:
                added.append(path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, OSError):
                continue
    return "\n".join(added)


def abort_proposal(root: Path, report: dict[str, Any], base: str, base_head: str) -> dict[str, Any]:
    """Undo the proposal, return to the base branch, and block the pass.

    One exit for every refusal after the branch exists (out-of-scope producer,
    unproven correction, unauthorized cure), so a new refusal cannot ship a
    fourth restore path that forgets one of these four assertions.
    """
    residue = restore(root)
    _git(root, "checkout", base)
    if report.get("branch"):
        _git(root, "branch", "-D", report["branch"])
    report["branch"] = None
    report["base"]["head_after"] = _git(root, "rev-parse", "HEAD")["stdout"].strip()
    report["base"]["untouched"] = report["base"]["head_after"] == base_head
    # Assert the restore, never announce it: a refusal that leaves the bytes
    # behind is the failure it claims to have prevented.
    if residue or worktree_changes(root):
        report["refusals"].append(
            finding(
                root,
                "BUILD_RESTORE_FAILED",
                residue[0] if residue else "worktree",
                f"refused writes survived the restore: {residue}",
                "restore this checkout by hand before running any further pass",
            )
        )
    report["outcome"] = "blocked"
    return report


def build_pass(
    root: Path, skill: str, authorization: dict[str, str] | None = None
) -> dict[str, Any]:
    root = root.resolve()
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root),
        "git": git_identity(root),
        "mode": "build",
        "skill": skill,
        "outcome": "blocked",
        "doctor": [],
        "base": {},
        "branch": None,
        "producers": [],
        "corrections": [],
        "proof": [],
        "refusals": [],
        "filing_route": (
            f"corrections are PROPOSED on a branch under skills/{skill}/ and land "
            "only through the repository's own PR ceremony; this pass never "
            "commits to the base branch and never writes outside that directory"
        ),
    }

    blockers = build_doctor(root, skill)
    report["doctor"] = blockers
    if blockers:
        return report

    base = _git(root, "rev-parse", "--abbrev-ref", "HEAD")["stdout"].strip()
    base_head = _git(root, "rev-parse", "HEAD")["stdout"].strip()
    report["base"] = {"branch": base, "head_before": base_head}

    # Microsecond stamp, not `generated_utc`: two passes in the same second
    # would otherwise collide on the branch name and the second one would
    # report `blocked` for a reason that has nothing to do with the subject.
    branch = f"maintain/{skill}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
    if _git(root, "checkout", "-b", branch)["returncode"] != 0:
        report["doctor"].append(f"DOCTOR_BRANCH_REFUSED:{branch}")
        return report
    report["branch"] = branch

    scope = f"skills/{skill}/"
    producers = build_producers(root, skill)
    for relative in producers:
        outcome = _run([sys.executable, relative], root)
        changed = worktree_changes(root)
        escaped = [path for path in changed if not path.startswith(scope)]
        report["producers"].append(
            {
                "producer": relative,
                "returncode": outcome["returncode"],
                "changed": changed,
            }
        )
        if outcome["returncode"] != 0:
            report["refusals"].append(
                finding(
                    root,
                    "BUILD_PRODUCER_FAILED",
                    relative,
                    f"exit {outcome['returncode']}: {outcome['tail']}",
                    "fix the producer before proposing anything it generates",
                )
            )
        elif escaped:
            report["refusals"].append(
                finding(
                    root,
                    "BUILD_EDIT_SCOPE_REFUSED",
                    relative,
                    f"wrote outside {scope}: {', '.join(escaped)}",
                    f"BUILD may propose only under {scope}; regenerate the repository "
                    "artifact through its own gate instead",
                )
            )
        if report["refusals"]:
            break

    if report["refusals"]:
        return abort_proposal(root, report, base, base_head)

    proposed = [path for path in worktree_changes(root) if path.startswith(scope)]
    if proposed:
        # ed3c/skill-concerns#93: before the proposal is proven, it has to be
        # ADJUDICATED. Detection is the beginning of an adjudication, so a
        # proposal that introduces or alters an enforcement shape without
        # naming the measurement that chose that shape is refused here rather
        # than proven and shipped. `refuse()` is the shared decision every
        # BUILD carrier in this repository makes; there is no copy of it here.
        cure = cure_authorization.refuse(
            f"skills/{skill}",
            proposal_additions(root, scope),
            authorization,
            tree=root,
        )
        if cure is not None:
            report["refusals"].append(
                finding(root, cure.diagnostic, cure.subject, cure.detail, cure.action)
            )
            report["corrections"] = []
            return abort_proposal(root, report, base, base_head)
        # "One PR of PROVEN corrections" (pstack donor, step 6). Regenerated
        # bytes nobody re-ran are a proposal about a Skill, not a correction
        # to it, so the subject's own declared row runs against the proposal
        # before it becomes a commit.
        #
        # Only that row. `check_admissions.py` reds by construction here - the
        # admission receipt pins bytes BUILD just moved, and the re-stamp
        # (gen_admission.py -> admissions/) is a repository artifact outside
        # BUILD's edit scope on purpose. Re-stamping belongs to the landing
        # ceremony, not to a pass that may only propose.
        #
        # `.get(skill, ())` used to give "no row exists" and "the row ran
        # green" the identical shape in this report (both `proof: []`, zero
        # proof_findings). A skill absent from SKILL_CHECKS entirely proves
        # nothing, so absence is its own refusal rather than a silent
        # pass-through to a commit.
        if skill in run_all.SKILL_CHECKS:
            proof, proof_findings = drive_checks(
                root,
                [(f"skill:{skill}", list(argv)) for argv in run_all.SKILL_CHECKS[skill]],
            )
        else:
            proof, proof_findings = [], [
                finding(
                    root,
                    "BUILD_SKILL_UNCHECKED",
                    skill,
                    f"{skill} has no row in run_all.SKILL_CHECKS; there is no check to prove this proposal against",
                    "add a SKILL_CHECKS row for this skill before BUILD may propose corrections for it",
                )
            ]
        report["proof"] = proof
        if proof_findings:
            report["refusals"].extend(proof_findings)
            report["refusals"].append(
                finding(
                    root,
                    "BUILD_PROPOSAL_UNPROVEN",
                    f"skills/{skill}",
                    f"{len(proof_findings)} of the subject's own checks red on the proposal",
                    "a correction that reds the Skill's own row is a regression; fix the producer, not the receipt",
                )
            )
            return abort_proposal(root, report, base, base_head)
        _git(root, "add", "--", f"skills/{skill}")
        commit = _git(
            root,
            "commit",
            "-m",
            f"maintain({skill}): propose regenerated evidence\n\n"
            f"Producers: {', '.join(producers)}",
            identity=True,
        )
        head = _git(root, "rev-parse", "HEAD")["stdout"].strip()
        if commit["returncode"] != 0 or head == base_head:
            report["refusals"].append(
                finding(
                    root,
                    "BUILD_PROPOSAL_UNCOMMITTED",
                    branch,
                    f"commit exit {commit['returncode']}: {commit['tail']}",
                    "the proposal has to exist as a commit on the branch or it is not a proposal",
                )
            )
        report["corrections"] = proposed
        report["proposal_head"] = head

    _git(root, "checkout", base)
    report["base"]["head_after"] = _git(root, "rev-parse", "HEAD")["stdout"].strip()
    report["base"]["untouched"] = report["base"]["head_after"] == base_head
    if not report["base"]["untouched"] or worktree_changes(root):
        report["refusals"].append(
            finding(
                root,
                "BUILD_BASE_MUTATED",
                base,
                f"{base} moved {base_head} -> {report['base']['head_after']} during a proposal pass",
                "a proposal never lands; restore the base branch by hand",
            )
        )

    if report["refusals"]:
        report["outcome"] = "blocked"
    elif report["corrections"]:
        report["outcome"] = "changed"
    else:
        if report["branch"]:
            _git(root, "branch", "-D", report["branch"])
            report["branch"] = None
        report["outcome"] = "clean"
    return report


def write_report(report: dict[str, Any], report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = report["generated_utc"].replace(":", "").replace("-", "")
    name = (
        f"maintain-build-{report['skill']}-{stamp}.json"
        if report.get("mode") == "build"
        else f"maintain-skills-{stamp}.json"
    )
    path = report_dir / name
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    # Evidence is checked at its named location, not assumed.
    readback = json.loads(path.read_text(encoding="utf-8"))
    if readback["outcome"] != report["outcome"]:
        raise SystemExit(f"REPORT_READBACK_MISMATCH:{path}")
    return path


def log_line(report: dict[str, Any], path: Path) -> str:
    if report["mode"] == "build":
        return (
            f"maintain-build[{report['skill']}]: {report['outcome']} "
            f"producers={len(report['producers'])} "
            f"corrections={len(report['corrections'])} "
            f"refusals={len(report['refusals'])} "
            f"branch={report['branch']} "
            f"report={path}"
        )
    return (
        f"maintain-skills: {report['outcome']} "
        f"checks={len(report['checks'])} "
        f"pins={len(report['pins'])} "
        f"findings={len(report['findings'])} "
        f"unreachable={len(report['unreachable'])} "
        f"report={path}"
    )


# --------------------------------------------------------------------------
# selftest: planted drift must be detected, reported, and left alone


def selftest() -> int:
    root = REPO_ROOT
    before = scope_digest(root)
    scratch = Path(tempfile.mkdtemp(prefix="maintain-skills-selftest-"))
    checks: list[tuple[str, bool, str]] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append((name, passed, detail))

    try:
        copy = scratch / "tree"
        shutil.copytree(
            root, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
        )

        clean = sweep(copy, run_skill_checks=False, online=False)
        record(
            "positive_control_unmutated_copy_is_clean",
            clean["outcome"] == "clean",
            f"outcome={clean['outcome']} findings={[f['diagnostic'] for f in clean['findings']]}",
        )

        lock = json.loads(
            (copy / "intake" / "control-backup" / "source-lock.json").read_text(encoding="utf-8")
        )
        planted = copy / lock["locked_files"][0]["path"]
        planted.unlink()

        drifted = sweep(copy, run_skill_checks=False, online=False)
        diagnostics = [f["diagnostic"] for f in drifted["findings"]]
        absent = [f for f in drifted["findings"] if f["diagnostic"].endswith("_ABSENT")]
        record(
            "planted_drift_changes_the_outcome",
            drifted["outcome"] == "changed",
            f"outcome={drifted['outcome']}",
        )
        record(
            "planted_drift_has_a_distinct_diagnostic",
            bool(absent),
            f"diagnostics={diagnostics}",
        )
        record(
            "every_finding_names_a_path_line_destination",
            all(":" in f["destination"] for f in drifted["findings"]),
            f"destinations={[f['destination'] for f in drifted['findings']]}",
        )
        record(
            "planted_drift_destination_is_a_real_pin_not_a_guess",
            all(
                not f["destination"].startswith("NO_MATCHING_PIN:")
                for f in drifted["findings"]
            ),
            f"destinations={[f['destination'] for f in drifted['findings']]}",
        )
        record(
            "planted_drift_is_never_autofixed",
            not planted.exists(),
            f"{planted.relative_to(copy).as_posix()} still absent after the pass",
        )

        # SHADOW half, planted negative: the sweep executes the repository
        # gates, so a gate that writes into the subject is a write attempt
        # arriving through the sweep's own hands. It must be refused - the
        # report is untrusted, not merely noisy.
        shadow = scratch / "shadow"
        shutil.copytree(
            root, shadow, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
        )
        (shadow / "scripts" / "check_agents_hops.py").write_text(
            "import pathlib, sys\n"
            "root = pathlib.Path(sys.argv[sys.argv.index('--root') + 1])\n"
            "(root / 'skills' / 'PLANTED_SHADOW_WRITE.txt').write_text(\n"
            "    'a SHADOW pass must never write here\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        wrote = sweep(shadow, run_skill_checks=False, online=False)
        violations = [
            f for f in wrote["findings"] if f["diagnostic"] == "EDIT_SCOPE_VIOLATION"
        ]
        record(
            "planted_shadow_write_attempt_is_refused",
            wrote["outcome"] == "blocked" and bool(violations),
            f"outcome={wrote['outcome']} "
            f"diagnostics={[f['diagnostic'] for f in wrote['findings']]}",
        )
        record(
            "shadow_refusal_names_the_path_that_moved",
            bool(violations)
            and any(
                "skills/PLANTED_SHADOW_WRITE.txt" in row
                for row in wrote["edit_scope"]["moved"]
            ),
            f"moved={wrote['edit_scope']['moved']}",
        )

        # BUILD half. A purpose-built checkout, not the real tree: the
        # invariant under test is the guard, and the producers are data.
        build_root = scratch / "build"
        (build_root / "skills" / "demo-subject" / "scripts").mkdir(parents=True)
        (build_root / "policy").mkdir()
        (build_root / "policy" / "owned.json").write_text("{}\n", encoding="utf-8")
        (build_root / "skills" / "demo-subject" / "scripts" / "gen_evidence.py").write_text(
            "from pathlib import Path\n"
            "root = Path(__file__).resolve().parents[3]\n"
            "(root / 'skills' / 'demo-subject' / 'evidence.json').write_text(\n"
            "    '{\"regenerated\": true}\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        # check.py ships from the first commit so every build_pass call below
        # (positive, escape, regression) proves against the same static row -
        # SKILL_CHECKS is registered once and torn down once, in the finally.
        (build_root / "skills" / "demo-subject" / "check.py").write_text(
            "import json, sys\n"
            "from pathlib import Path\n"
            "body = json.loads((Path(__file__).parent / 'evidence.json').read_text())\n"
            "if body.get('regenerated') is not True:\n"
            "    print('EVIDENCE_REGRESSED:skills/demo-subject/evidence.json')\n"
            "    sys.exit(1)\n",
            encoding="utf-8",
        )
        _git(build_root, "init", "-q", "-b", "main")
        _git(build_root, "add", "-A")
        _git(build_root, "commit", "-q", "-m", "fixture", identity=True)
        base_head = _git(build_root, "rev-parse", "HEAD")["stdout"].strip()

        run_all.SKILL_CHECKS["demo-subject"] = (("skills/demo-subject/check.py",),)
        proposal = build_pass(build_root, "demo-subject")
        on_branch = _git(
            build_root, "show", f"{proposal['branch']}:skills/demo-subject/evidence.json"
        )
        record(
            "build_in_scope_correction_lands_on_a_branch",
            proposal["outcome"] == "changed"
            and proposal["corrections"] == ["skills/demo-subject/evidence.json"]
            and on_branch["returncode"] == 0,
            f"outcome={proposal['outcome']} branch={proposal['branch']} "
            f"corrections={proposal['corrections']}",
        )
        record(
            "build_never_mutates_the_base_branch",
            proposal["base"]["untouched"]
            and _git(build_root, "rev-parse", "HEAD")["stdout"].strip() == base_head
            and not worktree_changes(build_root),
            f"base={proposal['base']} dirty={worktree_changes(build_root)}",
        )

        # Planted negative: a producer that reaches outside the subject Skill.
        (build_root / "skills" / "demo-subject" / "scripts" / "gen_escape.py").write_text(
            "from pathlib import Path\n"
            "root = Path(__file__).resolve().parents[3]\n"
            "(root / 'policy' / 'owned.json').write_text('{\"owned\": false}\\n',\n"
            "    encoding='utf-8')\n",
            encoding="utf-8",
        )
        _git(build_root, "add", "-A")
        _git(build_root, "commit", "-q", "-m", "plant the escape", identity=True)
        escaped_head = _git(build_root, "rev-parse", "HEAD")["stdout"].strip()

        refused = build_pass(build_root, "demo-subject")
        diagnostics = [f["diagnostic"] for f in refused["refusals"]]
        record(
            "planted_build_out_of_scope_write_is_refused",
            refused["outcome"] == "blocked"
            and diagnostics == ["BUILD_EDIT_SCOPE_REFUSED"],
            f"outcome={refused['outcome']} refusals={diagnostics}",
        )
        record(
            "refused_build_pass_leaves_no_bytes_and_no_branch",
            (build_root / "policy" / "owned.json").read_text(encoding="utf-8") == "{}\n"
            and refused["branch"] is None
            and not worktree_changes(build_root)
            and _git(build_root, "rev-parse", "HEAD")["stdout"].strip() == escaped_head,
            f"branch={refused['branch']} dirty={worktree_changes(build_root)}",
        )
        # Planted negative: a producer whose output reds the subject's own
        # declared row. BUILD must refuse to commit bytes that regress the
        # Skill, or "proven corrections" is a word rather than a gate.
        (build_root / "skills" / "demo-subject" / "scripts" / "gen_escape.py").unlink()
        (build_root / "skills" / "demo-subject" / "scripts" / "gen_evidence.py").write_text(
            "from pathlib import Path\n"
            "root = Path(__file__).resolve().parents[3]\n"
            "(root / 'skills' / 'demo-subject' / 'evidence.json').write_text(\n"
            "    '{\"regenerated\": \"regressed\"}\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        (build_root / "skills" / "demo-subject" / "evidence.json").write_text(
            '{"regenerated": true}\n', encoding="utf-8"
        )
        _git(build_root, "add", "-A")
        _git(build_root, "commit", "-q", "-m", "plant the regression", identity=True)
        regressed_head = _git(build_root, "rev-parse", "HEAD")["stdout"].strip()
        unproven = build_pass(build_root, "demo-subject")
        record(
            "planted_unproven_correction_is_refused",
            unproven["outcome"] == "blocked"
            and "BUILD_PROPOSAL_UNPROVEN"
            in [f["diagnostic"] for f in unproven["refusals"]]
            and unproven["branch"] is None
            and not worktree_changes(build_root)
            and _git(build_root, "rev-parse", "HEAD")["stdout"].strip() == regressed_head,
            f"outcome={unproven['outcome']} "
            f"refusals={[f['diagnostic'] for f in unproven['refusals']]}",
        )
        # Planted control, ed3c/skill-concerns#93: the canonical refused case is
        # the copy-nearest-ratchet shape from the trigger chain. The producer is
        # healthy and its output PASSES the subject's own row, so the only thing
        # that can refuse this proposal is the cure-authorization gate - a proof
        # failure would prove nothing about this rule.
        (build_root / "skills" / "demo-subject" / "scripts" / "gen_evidence.py").write_text(
            "import json\n"
            "from pathlib import Path\n"
            "root = Path(__file__).resolve().parents[3]\n"
            f"body = json.loads({cure_authorization.COPY_NEAREST_RATCHET!r})\n"
            "body['regenerated'] = True\n"
            "(root / 'skills' / 'demo-subject' / 'evidence.json').write_text(\n"
            "    json.dumps(body, indent=2) + '\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        (build_root / "skills" / "demo-subject" / "evidence.json").write_text(
            '{"regenerated": true}\n', encoding="utf-8"
        )
        _git(build_root, "add", "-A")
        _git(build_root, "commit", "-q", "-m", "plant the copied ratchet", identity=True)
        ratchet_head = _git(build_root, "rev-parse", "HEAD")["stdout"].strip()

        unauthorized = build_pass(build_root, "demo-subject")
        record(
            "planted_unauthorized_cure_is_refused",
            unauthorized["outcome"] == "blocked"
            and cure_authorization.DIAGNOSTIC
            in [f["diagnostic"] for f in unauthorized["refusals"]]
            and unauthorized["branch"] is None
            and unauthorized["corrections"] == []
            and not worktree_changes(build_root)
            and _git(build_root, "rev-parse", "HEAD")["stdout"].strip() == ratchet_head,
            f"outcome={unauthorized['outcome']} "
            f"refusals={[f['diagnostic'] for f in unauthorized['refusals']]}",
        )
        record(
            "the_refusal_names_the_shapes_and_the_rule",
            any(
                "ratchet" in f["detail"] and "ed3c/skill-concerns#93" in f["detail"]
                for f in unauthorized["refusals"]
            ),
            f"details={[f['detail'] for f in unauthorized['refusals']]}",
        )

        # A SHADOW detection is the beginning of an adjudication, never its
        # conclusion: naming one must not unlock the same proposal.
        detected = build_pass(
            build_root,
            "demo-subject",
            {"kind": "shadow-detection", "ref": "ed3c/skill-concerns#93"},
        )
        record(
            "a_shadow_detection_never_authorizes_a_cure",
            detected["outcome"] == "blocked"
            and any(
                f["diagnostic"] == cure_authorization.DIAGNOSTIC
                and "SHADOW detections never authorize" in f["detail"]
                for f in detected["refusals"]
            ),
            f"refusals={[(f['diagnostic'], f['detail'][:60]) for f in detected['refusals']]}",
        )

        # Planted negative control: the SAME bytes with a valid authorization
        # reach the branch behind the existing proof gate, unchanged in every
        # other respect. Without this arm the refusal above could be a gate
        # that refuses everything.
        authorized = build_pass(
            build_root, "demo-subject", dict(cure_authorization.ADJUDICATED_AUTHORIZATION)
        )
        on_branch = _git(
            build_root, "show", f"{authorized['branch']}:skills/demo-subject/evidence.json"
        )
        record(
            "an_authorized_cure_reaches_the_branch_behind_the_proof_gate",
            authorized["outcome"] == "changed"
            and authorized["corrections"] == ["skills/demo-subject/evidence.json"]
            and on_branch["returncode"] == 0
            and "ratchet" in on_branch["stdout"]
            and authorized["proof"]
            and authorized["base"]["untouched"]
            and _git(build_root, "rev-parse", "HEAD")["stdout"].strip() == ratchet_head,
            f"outcome={authorized['outcome']} branch={authorized['branch']} "
            f"corrections={authorized['corrections']}",
        )

        del run_all.SKILL_CHECKS["demo-subject"]

        # Planted negative: a skill with proposable bytes but no row in
        # SKILL_CHECKS at all - never registered, not registered-empty. This
        # is the exact case ed3c/skill-concerns#62's monitor named: absence
        # must not read the same as "the row ran green".
        (build_root / "skills" / "unchecked-subject" / "scripts").mkdir(parents=True)
        (build_root / "skills" / "unchecked-subject" / "scripts" / "gen_thing.py").write_text(
            "from pathlib import Path\n"
            "root = Path(__file__).resolve().parents[3]\n"
            "(root / 'skills' / 'unchecked-subject' / 'thing.json').write_text(\n"
            "    '{}\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        _git(build_root, "add", "-A")
        _git(build_root, "commit", "-q", "-m", "add an unregistered skill", identity=True)
        unregistered_head = _git(build_root, "rev-parse", "HEAD")["stdout"].strip()
        assert "unchecked-subject" not in run_all.SKILL_CHECKS
        unregistered = build_pass(build_root, "unchecked-subject")
        record(
            "planted_unregistered_skill_is_refused_not_silently_proven",
            unregistered["outcome"] == "blocked"
            and "BUILD_SKILL_UNCHECKED"
            in [f["diagnostic"] for f in unregistered["refusals"]]
            and unregistered["branch"] is None
            and not worktree_changes(build_root)
            and _git(build_root, "rev-parse", "HEAD")["stdout"].strip() == unregistered_head,
            f"outcome={unregistered['outcome']} "
            f"refusals={[f['diagnostic'] for f in unregistered['refusals']]}",
        )
        record(
            "build_excludes_producers_that_write_repository_artifacts",
            all(
                not producer.endswith(REPOSITORY_PRODUCERS)
                for producer in build_producers(root, "spatial-loop-grounded")
            ),
            f"producers={build_producers(root, 'spatial-loop-grounded')}",
        )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    # The provider predicates run offline here: a pin that cannot go red is not
    # a pin. Absence (404) and unreadability (network, auth, rate limit) must
    # land in different buckets, and a pin that fell off the branch must red.
    record(
        "ref_state_separates_absence_from_unreadability",
        (
            ref_state(0, "")
            + ref_state(1, "gh: Not Found (HTTP 404)")
            + ref_state(1, "dial tcp: lookup api.github.com: no such host")
        )
        == "RESOLVEDUNRESOLVEDBLOCKED",
        "0 -> RESOLVED, 404 -> UNRESOLVED, anything else -> BLOCKED",
    )
    record(
        "ancestry_predicate_reds_when_the_pin_leaves_the_branch",
        [ancestry_ok(s) for s in ("identical", "ahead", "behind", "diverged")]
        == [True, True, False, False],
        "identical/ahead keep the pin reachable; behind/diverged do not",
    )

    record("no_residue_outlives_the_run", not scratch.exists(), f"scratch={scratch}")
    record(
        "edit_scope_held_on_the_real_tree",
        scope_digest(root) == before,
        f"digest={before}",
    )

    for name, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    failed = [name for name, passed, _ in checks if not passed]
    if failed:
        print(f"selftest FAILED: {len(failed)} assertion(s) did not hold: {failed}")
        return 1
    print("selftest OK: drift is detected, filed, and left alone")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "maintain-skills",
        help="where the report artifact is written and read back",
    )
    parser.add_argument("--offline", action="store_true", help="skip every provider pin")
    parser.add_argument(
        "--no-skill-checks",
        action="store_true",
        help="repository gates and pins only; skip each Skill's own validator and selftests",
    )
    parser.add_argument(
        "--pass",
        dest="build_skill",
        metavar="SKILL",
        help="BUILD mode: propose corrections for SKILL on a branch, inside "
        "skills/SKILL/ only. Without it the default SHADOW pass runs, which "
        "has no write verb at all.",
    )
    parser.add_argument(
        "--cure-authorization",
        dest="cure_authorization",
        metavar="KIND=REF",
        help="BUILD mode: the adjudication that authorizes an enforcement-shape "
        "cure, e.g. discriminating-measurement=ed3c/skill-concerns#93. Without it a "
        "proposal that introduces or alters a gate, ratchet, threshold, "
        "refusal or escape-hatch condition is refused. An operator adjudication "
        "is not typeable here (ed3c/skill-concerns#103): it needs a pinned subject "
        "and a resolvable artifact, so it arrives as a record in the proposal.",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    if args.build_skill:
        authorization = (
            cure_authorization.parse(args.cure_authorization)
            if args.cure_authorization
            else None
        )
        report = build_pass(args.root, args.build_skill, authorization)
        path = write_report(report, args.report_dir)
        print(log_line(report, path))
        for item in report["refusals"]:
            print(f"  {item['diagnostic']} {item['subject']} -> {item['destination']} :: {item['action']}")
        for item in report["corrections"]:
            print(f"  PROPOSED {item} on {report['branch']}")
        for blocker in report["doctor"]:
            print(f"  {blocker}")
        return {"clean": 0, "changed": 1, "blocked": 2}[report["outcome"]]

    report = sweep(
        args.root,
        run_skill_checks=not args.no_skill_checks,
        online=not args.offline,
    )
    path = write_report(report, args.report_dir)
    print(log_line(report, path))
    for item in report["findings"]:
        print(f"  {item['diagnostic']} {item['subject']} -> {item['destination']} :: {item['action']}")
    for item in report["unreachable"]:
        print(f"  UNREACHABLE {item['pin']} needs {item['prerequisite']} -> {item['destination']}")
    for blocker in report["doctor"]:
        print(f"  {blocker}")
    return {"clean": 0, "changed": 1, "blocked": 2}[report["outcome"]]


if __name__ == "__main__":
    raise SystemExit(main())
