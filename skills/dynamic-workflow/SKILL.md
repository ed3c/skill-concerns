---
name: dynamic-workflow
description: >
  Read a dispatch runtime and report what its lanes are doing - Claude Code
  Workflow waves and codex daemon sessions alike. Use when supervising, judging,
  or triaging dispatched background work: is a lane alive, stalled, dead, or
  complete, and what may a supervisor say about it. Reader-only: it never writes
  to the observed system, never gates a landing, and never repairs a lane.
---

# Dynamic Workflow

The supervision layer for dispatched work, as bytes instead of habit. Two
failures put it here: a clause-compliance judge that could not find the lane
prompts because they lived only inline in wave scripts, and a still-running run
misdiagnosed as crashed because liveness-reading knowledge for workflow runtimes
had never been written down.

## The one law

**The completion notification is the only death certificate.**

Silence, a missing artifact, and absence from a process list are each consistent
with still-running. A lane is therefore classified as one of four things, and
`dead` is reachable only through a death signature the runtime itself wrote:

| Class | Reached by | Severity |
|---|---|---|
| `complete` | a completion notification for this lane | S0 |
| `healthy` | no notification, no death signature, quiet within the threshold | S0 |
| `stalled-suspect` | no notification, no death signature, quiet past the threshold | S1 |
| `dead` | no notification **and** a death signature | S2 |

Age never produces `dead`. That is the whole point.

## Doctor — is this lane worth reading?

```bash
python3 skills/dynamic-workflow/scripts/liveness_driver.py --selftest
```

Run this first whenever anything looks off. It replays every classification law
against planted stuck / dead / healthy fixtures and inverts each negative
control, so a weakened assertion goes red instead of quietly agreeing with you.

## Drive — observe a run

```bash
python3 skills/dynamic-workflow/scripts/liveness_driver.py --observe <run-record-path>
```

The runtime is auto-detected from the record's own shape; pass `--runtime` to
force it. Ages come from the timestamps *inside* the records, never from file
mtime — one runtime bulk-rewrites its rollup file's mtime for every session at
once, and a checkout rewrites all of them.

## Evidence — where the proof goes

The report is written to `$DYNAMIC_WORKFLOW_EVIDENCE`, defaulting to
`$TMPDIR/dynamic-workflow/observation-<runtime>-<id>.json`, and the driver
prints that path as its last line. Nothing removes it: **Cleanup is N/A by
construction** for a reader, which creates no instance to tear down.

Launch is N/A for the same reason. The run being observed is already running or
already finished; a reader attaches to its record and starts nothing.

## What a supervisor may say

The delivery discipline is [`references/portable-supervision-policy.md`](references/portable-supervision-policy.md):
stage-boundary only, receipt-quote plus exactly one question, one delivery per
boundary, no mid-flight injection, actor-unaware judging, S0/S1/S2 severities,
and the five judge rules (v3). The dispatcher references the two prompt files by
path — [`references/prompts/monitor-prompt.md`](references/prompts/monitor-prompt.md)
and [`references/prompts/judge-prompt.md`](references/prompts/judge-prompt.md) —
rather than inlining them; inlining is the original defect.

## Two lenses on one lane

This Skill reads a codex cook session at the **runtime** layer only: session
liveness, spawn surface, death signatures, the falsely-alive shapes. Everything
about whether the work is *correct and legal by its own playbook* belongs to
[`control-noodle`](../control-noodle/SKILL.md)'s Monitor mode, and
[`domain/dispatch-runtime-topology.json`](domain/dispatch-runtime-topology.json)
points there instead of restating it. Same lane, two lenses; a restated copy is
the drift a single-owner discipline exists to prevent.

## Findings, and why this reader cannot fix itself

- **Observed-system findings** are reported and never applied.
- **Lens-drift findings** — a stale observation guide, a threshold misfiring —
  are mechanically FILED with a strict destination and `owner=dynamic-workflow`.
  The daily maintenance sweep consumes them on its own cadence; being admitted
  is what enrolls this Skill in that sweep.
- **Narrow exception, triggered not applied:** if the driver's own selftest is
  red at observation time, the report degrades itself to `lens: lens-suspect`
  and sets `maintain_pass: SCHEDULED`. The pass still lands through the full
  change ceremony. Trigger automation keeps every gate; application automation
  does not — a reader that rewrites its own lens until a finding disappears is
  self-laundering.

## Knowledge placement

- **L0 procedural** — [`references/portable-supervision-policy.md`](references/portable-supervision-policy.md),
  instantiating `spatial-loop-grounded`'s supervision kernel (K1, K10) rather
  than replacing it.
- **L1 domain knowledge** — [`domain/dispatch-runtime-topology.json`](domain/dispatch-runtime-topology.json):
  both runtimes' observables, self-defined, with the counts each shape was read
  from.
- **L2 execution + assertions** — [`scripts/liveness_driver.py`](scripts/liveness_driver.py)
  plus the two prompt files the dispatcher runs.
- **Physical receipts** — [`receipts.json`](receipts.json).
