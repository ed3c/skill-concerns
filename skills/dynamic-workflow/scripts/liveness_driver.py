#!/usr/bin/env python3
"""L2 - execution + assertions for dispatch-runtime liveness.

The executable Doctor of this reader-only Skill. It OBSERVEs (reads a wave
journal or a session ledger), CLASSIFIEs (complete / healthy / stalled-suspect /
dead), ASSERTs the law the L0 policy demands, and PERSISTs an observation
receipt at a named location. It never writes to the observed system.

The load-bearing law is K10: **the completion notification is the only death
certificate**. Age never produces `dead`; only a death signature does. That is
the whole reason `stalled-suspect` exists as a distinct class, and
`--selftest` proves the assertion can go red by inverting each negative control.

Ages come from the newest ISO-8601 `timestamp` *inside* the records, never from
file mtime: a checkout rewrites mtime, and one observed runtime bulk-rewrites
its own rollup file's mtime for every session at once.

Usage:
  liveness_driver.py --selftest
  liveness_driver.py --observe <path> [--runtime auto|claude-code-workflow|codex-noodle-session]
                     [--now <iso>] [--out <file>]
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = SKILL_ROOT / "domain" / "dispatch-runtime-topology.json"

# Severity ladder from the L0 policy: S0 observe, S1 warn, S2 review.
SEVERITY = {
    "complete": "S0",
    "healthy": "S0",
    "stalled-suspect": "S1",
    "dead": "S2",
}

CLAUDE_DEATH_SIGNATURES = (
    "[Request interrupted by user]",
    "[Request interrupted by user for tool use]",
)


@dataclass
class Assertion:
    name: str
    passed: bool
    detail: str


@dataclass
class Lane:
    lane: str
    lane_class: str
    severity: str
    age_seconds: float | None
    receipt: str


def stall_threshold() -> int:
    return int(json.loads(TOPOLOGY.read_text(encoding="utf-8"))["stall_threshold_seconds"])


def parse_iso(value: str) -> float:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.timestamp()


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    if not path.is_file():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


# --------------------------------------------------------------------------
# The law. Everything else feeds this.
# --------------------------------------------------------------------------
def classify(
    has_completion: bool,
    death_signature: str | None,
    age_seconds: float | None,
    threshold: int,
) -> str:
    """K10: only a completion notification ends a lane; only a death signature kills it.

    A lane with no completion and no death signature is `stalled-suspect` once it
    is quiet past the threshold -- never `dead`, however long the silence runs.
    """
    if has_completion:
        return "complete"
    if death_signature is not None:
        return "dead"
    if age_seconds is not None and age_seconds > threshold:
        return "stalled-suspect"
    return "healthy"


def assert_stalled_suspect_is_never_death(age_seconds: float, threshold: int) -> Assertion:
    verdict = classify(False, None, age_seconds, threshold)
    return Assertion(
        "stalled_suspect_is_never_death",
        verdict == "stalled-suspect",
        f"a lane quiet for {age_seconds:.0f}s with no death signature classified {verdict!r} "
        "(K10: silence is consistent with still-running)",
    )


def assert_death_needs_a_signature(signature: str | None, threshold: int) -> Assertion:
    verdict = classify(False, signature, 0.0, threshold)
    return Assertion(
        "death_needs_a_signature",
        verdict == "dead",
        f"a lane carrying signature {signature!r} classified {verdict!r}",
    )


def assert_completion_wins(threshold: int) -> Assertion:
    verdict = classify(True, CLAUDE_DEATH_SIGNATURES[0], 10**9, threshold)
    return Assertion(
        "completion_notification_is_terminal",
        verdict == "complete",
        f"a lane with a completion notification classified {verdict!r} even against age and a signature",
    )


# --------------------------------------------------------------------------
# Runtime readers
# --------------------------------------------------------------------------
def detect_runtime(path: Path) -> str:
    if (path / "journal.jsonl").is_file():
        return "claude-code-workflow"
    if (path / "canonical.ndjson").is_file() or (path / "events.ndjson").is_file():
        return "codex-noodle-session"
    raise SystemExit(f"ABSENT: no known dispatch-runtime record under {path}")


def observe_claude_workflow(path: Path, now: float, threshold: int) -> list[Lane]:
    journal = read_jsonl(path / "journal.jsonl")
    if not journal:
        raise SystemExit(f"ABSENT: empty or unreadable wave journal under {path}")
    started = [e["agentId"] for e in journal if e.get("type") == "started" and e.get("agentId")]
    completed = {e["agentId"] for e in journal if e.get("type") == "result" and e.get("agentId")}

    lanes: list[Lane] = []
    for agent_id in started:
        transcript = read_jsonl(path / f"agent-{agent_id}.jsonl")
        stamps = [parse_iso(r["timestamp"]) for r in transcript if isinstance(r.get("timestamp"), str)]
        age = (now - max(stamps)) if stamps else None
        tail = json.dumps(transcript[-1], ensure_ascii=False) if transcript else ""
        signature = next((s for s in CLAUDE_DEATH_SIGNATURES if s in tail), None)
        has_completion = agent_id in completed
        receipt = (
            f'journal.jsonl: {{"type": "result", "agentId": "{agent_id}"}}'
            if has_completion
            else (f"agent-{agent_id}.jsonl tail: {signature}" if signature else f"agent-{agent_id}.jsonl tail: {tail[:160]}")
        )
        lane_class = classify(has_completion, signature, age, threshold)
        lanes.append(Lane(agent_id, lane_class, SEVERITY[lane_class], age, receipt))
    return lanes


def observe_codex_session(path: Path, now: float, threshold: int) -> list[Lane]:
    canonical = read_jsonl(path / "canonical.ndjson")
    events = read_jsonl(path / "events.ndjson")
    stamps = [
        parse_iso(r["timestamp"])
        for r in canonical + events
        if isinstance(r.get("timestamp"), str)
    ]
    age = (now - max(stamps)) if stamps else None
    has_completion = any(r.get("type") == "result" for r in canonical)

    # K10 applies uniformly: meta.json status/health/alive are a rollup stamp,
    # never observed at read time (this is documented for `exited` in L1 and
    # must hold just as much for `failed` -- the same bulk-rewritten pass
    # writes both). The only signature this reader trusts is a record inside
    # the true event ledger itself: canonical.ndjson's own tail entry, the
    # same "last thing recorded, with nothing after it" shape the Claude-code
    # transcript-tail signature uses.
    tail_type = canonical[-1].get("type") if canonical else None
    signature = "canonical.ndjson tail: {\"type\": \"error\"}" if not has_completion and tail_type == "error" else None

    meta_path = path / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}

    receipt = (
        f'canonical.ndjson: {{"type": "result", "message": "{next((r.get("message") for r in canonical if r.get("type") == "result"), "")}"}}'
        if has_completion
        else (signature or f'meta.json: {{"status": {meta.get("status")!r}, "alive": {meta.get("alive")!r}}} (stamped, not observed)')
    )
    lane_class = classify(has_completion, signature, age, threshold)
    return [Lane(path.name, lane_class, SEVERITY[lane_class], age, receipt)]


# --------------------------------------------------------------------------
# Selftest: positive controls + inverted negative controls
# --------------------------------------------------------------------------
def _expect_false(a: Assertion, label: str) -> Assertion:
    return Assertion(f"negative_control:{label}", not a.passed, a.detail)


def selftest(verbose: bool = True) -> int:
    threshold = stall_threshold()
    fixtures = SKILL_ROOT / "evals" / "fixtures"
    # Fixture clock: every fixture record carries an absolute timestamp, so the
    # planted ages are deterministic across checkouts (mtime is not).
    now = parse_iso("2026-09-01T12:00:00Z")

    healthy = observe_claude_workflow(fixtures / "healthy-wave", now, threshold)
    stuck = observe_claude_workflow(fixtures / "stuck-wave", now, threshold)
    dead = observe_claude_workflow(fixtures / "dead-wave", now, threshold)
    codex_live = observe_codex_session(fixtures / "codex-healthy-session", now, threshold)
    codex_stale = observe_codex_session(fixtures / "codex-stale-stamp-session", now, threshold)
    codex_dead = observe_codex_session(fixtures / "codex-dead-session", now, threshold)
    codex_failed_stamp = observe_codex_session(fixtures / "codex-failed-stamp-not-dead-session", now, threshold)

    checks: list[Assertion] = [
        # unit-level law
        assert_stalled_suspect_is_never_death(3.5 * 3600, threshold),
        assert_stalled_suspect_is_never_death(72 * 3600, threshold),
        assert_death_needs_a_signature(CLAUDE_DEATH_SIGNATURES[0], threshold),
        assert_completion_wins(threshold),
        # planted fixtures, red-then-green
        Assertion(
            "fixture_healthy_wave_is_clean",
            [lane.lane_class for lane in healthy] == ["complete", "healthy"],
            f"healthy fixture classified {[lane.lane_class for lane in healthy]}",
        ),
        Assertion(
            "fixture_stuck_wave_is_stalled_suspect_not_dead",
            [lane.lane_class for lane in stuck] == ["stalled-suspect"]
            and stuck[0].age_seconds is not None
            and stuck[0].age_seconds > 3 * 3600,
            f"3h-frozen-but-alive fixture classified {[lane.lane_class for lane in stuck]} "
            f"at age {stuck[0].age_seconds:.0f}s",
        ),
        Assertion(
            "fixture_dead_wave_is_dead",
            [lane.lane_class for lane in dead] == ["dead"],
            f"death-signature fixture classified {[lane.lane_class for lane in dead]}",
        ),
        Assertion(
            "fixture_codex_healthy_is_complete",
            [lane.lane_class for lane in codex_live] == ["complete"],
            f"codex completed-session fixture classified {[lane.lane_class for lane in codex_live]}",
        ),
        Assertion(
            "fixture_codex_stale_stamp_is_stalled_suspect",
            [lane.lane_class for lane in codex_stale] == ["stalled-suspect"],
            "a session stamped status=running/alive=true whose ledger is 46h silent classified "
            f"{[lane.lane_class for lane in codex_stale]} - the stamp is not believed, and silence is not death",
        ),
        Assertion(
            "fixture_codex_dead_is_dead_from_ledger_tail",
            [lane.lane_class for lane in codex_dead] == ["dead"],
            f"a session whose canonical.ndjson tail record is type=error classified {[lane.lane_class for lane in codex_dead]}",
        ),
        Assertion(
            "fixture_codex_failed_stamp_alone_is_not_dead",
            [lane.lane_class for lane in codex_failed_stamp] == ["stalled-suspect"],
            "a session stamped status=failed whose canonical.ndjson tail is a plain action record "
            f"(no ledger error, no result) classified {[lane.lane_class for lane in codex_failed_stamp]} "
            "- the meta.json stamp alone must never promote to dead",
        ),
        Assertion(
            "severity_ladder_is_wired",
            [lane.severity for lane in stuck + dead + healthy] == ["S1", "S2", "S0", "S0"],
            f"severities {[lane.severity for lane in stuck + dead + healthy]}",
        ),
        # negative controls: each MUST be false, proving the assertions go red
        _expect_false(
            Assertion("age_alone_kills", classify(False, None, 10**9, threshold) == "dead", ""),
            "age alone must never yield dead",
        ),
        _expect_false(
            Assertion("silence_kills_at_threshold", classify(False, None, threshold + 1, threshold) == "dead", ""),
            "a lane one second past the threshold must not be dead",
        ),
        _expect_false(
            Assertion("signature_ignored", classify(False, "sig", 0.0, threshold) == "healthy", ""),
            "a death signature must not read as healthy",
        ),
        _expect_false(
            Assertion(
                "stale_stamp_reads_healthy",
                codex_stale[0].lane_class == "healthy",
                "the session stamped alive=true/health=green must not read as healthy: its ledger is 46h silent",
            ),
            "a stamped alive field must never become liveness evidence",
        ),
        _expect_false(
            Assertion(
                "failed_stamp_alone_reads_dead",
                codex_failed_stamp[0].lane_class == "dead",
                "the session stamped status=failed with no ledger error tail must not read as dead: "
                "the stamp is the same untrusted rollup pass as status=exited",
            ),
            "a stamped failed status must never become a death certificate on its own",
        ),
    ]

    failed = [c for c in checks if not c.passed]
    if verbose:
        for c in checks:
            print(f"[{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")
    if failed:
        if verbose:
            print(f"selftest FAILED: {len(failed)} assertion(s) did not hold")
        return 1
    if verbose:
        print("selftest OK: every assertion holds and every negative control went red")
    return 0


# --------------------------------------------------------------------------
# Observation mode
# --------------------------------------------------------------------------
def evidence_dir() -> Path:
    """The named location observation receipts survive at.

    Cleanup is N/A by construction for a reader: nothing removes these.
    """
    configured = os.environ.get("DYNAMIC_WORKFLOW_EVIDENCE")
    base = Path(configured) if configured else Path(os.environ.get("TMPDIR", "/tmp")) / "dynamic-workflow"
    return base


def observe(path: Path, runtime: str, now: float, out: Path | None) -> dict:
    threshold = stall_threshold()
    runtime = detect_runtime(path) if runtime == "auto" else runtime
    reader = {
        "claude-code-workflow": observe_claude_workflow,
        "codex-noodle-session": observe_codex_session,
    }[runtime]
    lanes = reader(path, now, threshold)

    # Adjudication 3: the lens degrades itself when its own selftest is red
    # NOW. Triggered, never applied -- the maintain pass is scheduled, not run.
    # selftest() reads the bundled fixtures via the same ABSENT-raising readers
    # used on a real subject; if the fixtures themselves are missing, that is
    # still "the lens is broken", not a crash of the real observation.
    try:
        lens_ok = selftest(verbose=False) == 0
    except SystemExit:
        lens_ok = False
    findings = []
    if not lens_ok:
        findings.append(
            {
                "type": "lens-drift",
                "owner": "dynamic-workflow",
                "destination": "skills/dynamic-workflow/scripts/liveness_driver.py:selftest",
                "severity": "S2",
                "detail": "the lens selftest is red at observation time; this report is lens-suspect",
                "action": "SCHEDULED maintain pass through the full change ceremony - never an inline edit",
            }
        )

    report = {
        "schema_version": 1,
        "skill": "dynamic-workflow",
        "runtime": runtime,
        "subject": str(path),
        "observed_at": datetime.fromtimestamp(now, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
        "stall_threshold_seconds": threshold,
        "lens": "ok" if lens_ok else "lens-suspect",
        "maintain_pass": "NOT_SCHEDULED" if lens_ok else "SCHEDULED",
        "lanes": [
            {
                "lane": lane.lane,
                "class": lane.lane_class,
                "severity": lane.severity,
                "age_seconds": None if lane.age_seconds is None else round(lane.age_seconds, 3),
                "receipt": lane.receipt,
            }
            for lane in lanes
        ],
        "summary": {
            klass: sum(1 for lane in lanes if lane.lane_class == klass)
            for klass in ("complete", "healthy", "stalled-suspect", "dead")
        },
        "findings": findings,
    }

    target = out or (evidence_dir() / f"observation-{runtime}-{path.name}.json")
    target_resolved = target.resolve() if target.is_absolute() else (Path.cwd() / target).resolve()
    subject_resolved = path.resolve()
    if target_resolved == subject_resolved or subject_resolved in target_resolved.parents:
        raise SystemExit(
            f"REFUSED: --out {target} resolves inside the observed subject {path}; "
            "the reader never writes to the observed system (docstring line 7)"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report["evidence_path"] = str(target)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--observe", type=Path)
    parser.add_argument(
        "--runtime",
        default="auto",
        choices=["auto", "claude-code-workflow", "codex-noodle-session"],
    )
    parser.add_argument("--now", help="ISO-8601 observation clock; defaults to real now")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if args.observe:
        now = parse_iso(args.now) if args.now else datetime.now(tz=timezone.utc).timestamp()
        report = observe(args.observe.resolve(), args.runtime, now, args.out)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"evidence: {report['evidence_path']}")
        return 0
    parser.print_usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
