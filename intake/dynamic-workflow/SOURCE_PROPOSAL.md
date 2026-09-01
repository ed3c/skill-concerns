# Owner design brief — `dynamic-workflow`

Source kind: owner design brief. There is no upstream Git source to freeze: the
knowledge being admitted exists today only as inline text inside dispatch wave
scripts and as an un-codified reading habit. This file is the frozen source.

## Physical trigger

Two failures, one missing home.

1. The wave-10 clause-compliance judge could not find the lane prompts. They live
   only inline in workflow scripts, so the judge marked its own rule
   identification inference-grade rather than byte-grade.
2. A dispatch run was misdiagnosed as crashed from artifact and process absence
   while it was still running; manual work then raced its own land agents
   (`ed3c/noodles#243`, `#244`, carried as the `still-running-not-crashed`
   receipt of `spatial-loop-grounded`). Liveness-reading knowledge for workflow
   runtimes had never been codified, so the misread had nothing to fail against.

The same supervision must now run over **two** runtimes: Claude Code Workflow
waves and codex-driven daemon sessions.

## What this Skill is

A **reader**. It observes dispatch runtimes and reports; it never writes to the
systems it observes, never gates a landing, and never repairs a lane.

Authored under the pinned `create-verification-skill` procedure
(`policy/upstream-pins.json`), adapted read-only:

| create-verification-skill section | dynamic-workflow adaptation |
|---|---|
| Launch | **N/A by construction** — a reader starts nothing. The runtime is already running or already finished; the skill attaches to its on-disk journal. |
| Doctor | **liveness** — is this lane worth reading, and is it alive, stalled, dead, or complete? |
| Drive | **observation** — enumerate lanes from the journal, classify each, no writes. |
| Evidence | **receipts** — an observation report written to a named location that survives the run. |
| Cleanup | **N/A by construction** — a reader creates no instance, so there is nothing to tear down; and evidence is never removed. |

## Concern split requested

- **L0 procedural** — the supervision policy as versioned bytes: stage-boundary
  feedback, receipt-quote plus a single question, S0/S1/S2 severities, no
  mid-flight injection, actor-unaware judging, and the five judge rules (v3).
  Plus the three owner adjudications of 2026-09-01 recorded on
  `ed3c/skill-concerns#59`.
- **L1 domain topology** — both runtimes' observables, self-defined, including
  the healthy / stalled-suspect / dead shapes and the stamped-field hazards.
  Entries covering codex cook sessions **point to `control-noodle`** for ceremony
  semantics and never restate them.
- **L2 execution + assertions** — a liveness driver with `--selftest` over
  planted stuck / dead / healthy fixtures, plus the monitor and judge prompt
  files the dispatcher references by path instead of inlining.

## Owner adjudications (2026-09-01, `ed3c/skill-concerns#59`)

1. **Runtime / ceremony boundary.** dynamic-workflow watches the noodles
   schedule and execute skills at the RUNTIME layer only — session liveness,
   spawn surface, death signatures, falsely-dead versus dead shapes. It does NOT
   own the CEREMONY layer — frontier/winners correctness, cycle-receipt verbatim
   discipline, marker-transition legality, handoff ceremony — which stays with
   `control-noodle`'s Monitor mode. Same lane, two lenses. L1 entries covering
   cook sessions must POINT to `control-noodle`, never restate it.
2. **Filing, not reflex.** An observation-time finding does not invoke
   `maintain-verification-skill`. The reader stays a reader; an auto-maintain
   path would let the monitor rewrite its own lens until a finding disappears.
   Only lens-drift findings are maintain territory, and they are mechanically
   FILED with a strict destination and owner `dynamic-workflow`; the landed daily
   maintain sweep consumes them on its own cadence.
3. **Trigger, not apply.** One narrow exception: when the driver's own selftest
   goes red mid-observation, the observation report auto-degrades itself to
   `lens-suspect` and one immediate maintain pass is SCHEDULED — landing through
   the full PR and gate ceremony, never an inline edit. Trigger automation keeps
   every gate; application automation does not.

## Physical acceptance requested

- Full admission journey: source lock, three layers, hollow-mutation tests per
  the `control-code-intel` precedent, registry/routing/hub, `gen_admission`,
  `run_all` PASS.
- The `create-verification-skill` step-4 bar: the generated skill's own
  instructions executed once end to end against a REAL completed workflow run's
  journal, with evidence surviving at its named location.
- Planted negatives: a journal frozen three hours or more reports
  `stalled-suspect` WITHOUT declaring death; a journal carrying a death
  signature reports `dead`; a healthy journal reports clean.
- Not claimed at admission: the dispatcher-side wave script that references the
  admitted prompt files by path. That byte lives in the dispatcher's harness,
  not in this repository, and is filed for the dispatcher's ledger append.
