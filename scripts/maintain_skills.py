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
is the mechanical reader for that claim). Drift leaves here as a finding with a
destination, never as a patch: nothing in this file writes to the subject tree.

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

from common import REPO_ROOT, digest_entries, regular_files, tree_digest  # noqa: E402
import run_all  # noqa: E402


REPO_GATES = ("check_agents_hops.py", "check_skill_bundles.py", "check_admissions.py")

# Everything the sweep reads as subject and must leave byte-identical.
EDIT_SCOPE = ("skills", "admissions", "intake", "contracts", "policy", "registry.json")

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


def scope_digest(root: Path) -> str:
    entries: list[dict[str, str]] = []
    for relative in EDIT_SCOPE:
        path = root / relative
        if path.is_dir():
            entries.extend(digest_entries(root, regular_files(path)))
        elif path.is_file():
            entries.extend(digest_entries(root, [path]))
    return tree_digest(entries)


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
        commit = pin["pinned_commit"]
        if not online:
            unreachable.append(
                {
                    "pin": pin["id"],
                    "skill": repository,
                    "prerequisite": "network + gh auth (run without --offline)",
                    "destination": locate_destination(root, commit),
                }
            )
            continue

        head = _run(
            ["gh", "api", f"repos/{repository}/commits/{branch}", "--jq", ".sha"], root, 60
        )
        if head["returncode"] != 0:
            unreachable.append(
                {
                    "pin": pin["id"],
                    "skill": repository,
                    "prerequisite": f"provider readable: {head['tail']}",
                    "destination": locate_destination(root, commit),
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
                    "destination": locate_destination(root, commit),
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
                        "destination": locate_destination(root, watched["blob_sha"]),
                    }
                )
                results.append({"pin": watched["path"], "skill": repository, "state": "BLOCKED"})
                continue
            current = blob["stdout"].strip()
            results.append(
                {"pin": watched["path"], "skill": repository, "state": current}
            )
            if current != watched["blob_sha"]:
                findings.append(
                    finding(
                        root,
                        "UPSTREAM_WATCHED_FILE_CHANGED",
                        watched["blob_sha"],
                        f"{repository}:{watched['path']} is blob {current}; the pin names {watched['blob_sha']}",
                        pin.get("action_on_drift", "re-read the pinned upstream file"),
                    )
                )
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

    before = scope_digest(root)
    checks, check_findings = drive_checks(root, check_rows(root, run_skill_checks))
    ref_pins, ref_findings, ref_unreachable = check_refs(root, online)
    upstream_pins, upstream_findings, upstream_unreachable = check_upstream(root, online)
    after = scope_digest(root)

    report["checks"] = checks
    report["pins"] = ref_pins + upstream_pins
    report["findings"] = check_findings + ref_findings + upstream_findings
    report["unreachable"] = ref_unreachable + upstream_unreachable
    report["edit_scope"] = {
        "digest_before": before,
        "digest_after": after,
        "held": before == after,
    }

    if not report["edit_scope"]["held"]:
        report["findings"].insert(
            0,
            finding(
                root,
                "EDIT_SCOPE_VIOLATION",
                "registry.json",
                f"subject digest moved {before} -> {after} during the pass",
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


def write_report(report: dict[str, Any], report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = report["generated_utc"].replace(":", "").replace("-", "")
    path = report_dir / f"maintain-skills-{stamp}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    # Evidence is checked at its named location, not assumed.
    readback = json.loads(path.read_text(encoding="utf-8"))
    if readback["outcome"] != report["outcome"]:
        raise SystemExit(f"REPORT_READBACK_MISMATCH:{path}")
    return path


def log_line(report: dict[str, Any], path: Path) -> str:
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
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

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
