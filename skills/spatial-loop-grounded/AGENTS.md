# AGENTS.md — spatial-loop-grounded

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — provenance, receipt chain, hillclimb rule.
2. [`SKILL.md`](SKILL.md) — the grounded clauses in trigger form (count-tied to `references/portable-supervision-kernel.md`, so read the count off the file rather than off this line).
3. [`receipts.json`](receipts.json) — the exact provider receipts every clause binds to.
4. [`skill.json`](skill.json) — declared paths and executable route.
5. Read scripts, tests, and eval cases only when changing behavior.

## Stop laws

- A clause without a receipt binding does not enter this Skill, whatever its upstream quality.
- Receipts regenerate through their producers; hand-editing evidence is laundering.
- The upstream skills-shared body is the method owner; restating it here is drift, pointing at it is correct.
- Edits that weaken a trigger form, orphan a receipt, or erase provenance fail the validator; that is the hillclimb gate, not a formality.
- Session receipts prove one environment; portability claims require new receipts.
- A value claim for these clauses needs a without-skill control arm. A single-armed
  green measures the actor+clauses pair, never the clauses. On the rubric the
  2026-09-01 judge actually held, the arms tie on every physical criterion, so that
  claim is UNPROVEN, not established — do not cite a campaign green as evidence the
  clauses contributed.
- A criterion written after a wave ran can be fitted to that wave's runs, so its
  arm delta describes those runs and proves nothing. The wider rubric added under
  ed3c/skill-concerns#50 breaks the physical tie (`oracle_arm_scores` 1.0 vs 0.8333)
  by catching one gratuitous retry and one unlogged self-report, both in the without
  arm — that is a description of six runs, not evidence. Only criteria fixed before
  a wave runs can carry a value claim.

## Completion

**Every time** — hermetic, no live agents, seconds:

- `python3 skills/spatial-loop-grounded/scripts/validate_spatial_loop_grounded.py`
- `python3 -m unittest discover -s skills/spatial-loop-grounded/tests`
- `python3 skills/spatial-loop-grounded/scripts/ab_campaign.py selftest`
- `python3 skills/spatial-loop-grounded/scripts/ab_campaign.py score`

Report clause inventory, receipt bindings, every hollow-mutation control outcome,
the per-arm scores, the judge/mechanical-oracle agreement, and the treatment-trace
counts. All four read committed bytes; none of them runs an actor or a judge.

**Once per wave** — needs live actors and a live judge, costs real money, and is
NOT part of hermetic `run_all`: `ab_campaign.py --campaign <dir> stage` →
run the actors → `collect` → `judge-inputs` → judge → `score` → `receipt` →
`gen_ledger.py`. Run this when a wave is being run, never as a checklist tick.

Before scoring those runs, read the two interpretation-time caveats in the
protocol every campaign spec names (`protocol` in `spec.json`,
`docs/behavioral-eval-protocol.md`): the call log records mistyped calls the
client never dispatched, and criteria frozen before wave 2 were still shaped
after wave 1. The validator resolves that path and reds if either caveat
leaves the document, so the reference is a reader and not a citation.

**This step retires when** two waves have run and the second one's judged
criteria — the ones frozen in its spec before its actors ran — return the same
answer as the first. Until then a single n=3 null result is the only campaign
evidence this skill has, which is why `evals/behavioral-campaigns/ab-wave2/`
exists (`n_per_arm: 6`, staged, no runs). A third wave is not owed by this rule;
a contradicting second wave is.

Never hand-edit a campaign receipt or the ledger — `ab_campaign.py receipt` and
`gen_ledger.py` are their producers.
