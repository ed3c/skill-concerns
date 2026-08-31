# Behavioral eval protocol (pstack-style)

Textual evals (hollow mutations) prove a skill's BYTES cannot silently degrade.
Behavioral evals prove the skill changes AGENT BEHAVIOR. Both are required;
only the second justifies trusting a skill in real work.

## Mechanics

1. A coordinator (workflow script) builds the rubric from the skill's clauses
   (`evals/behavioral.json` pins scenario, bait, pass/fail rubric, oracle).
2. Actor sub-agents receive the skill content as loaded context plus a
   DISGUISED task in an innocuously named directory - no eval vocabulary
   anywhere the actor can see: an actor that knows it is being tested changes
   behavior and the receipt is worthless.
3. The oracle is PHYSICAL: fixture commands write an append-only call log;
   the judge reads the log and filesystem state, never the actor's narrative.
   Self-report is not evidence.
4. The judge is a DIFFERENT model than the actor (single-model bias control),
   scoring each scenario strictly against the pinned rubric.
5. Scores land as a campaign receipt in `evals/behavioral-campaigns/` -
   scenario, actor model, judge model, verdicts, log digests. The admission's
   hillclimb history plus these campaign receipts are the skill's score curve.
6. Hill-climb: when a scenario fails, the clause (not the rubric) is the
   default suspect - improve the skill text, re-run the campaign, iterate to
   the target score. Rubric edits require their own justification receipt.
7. Run campaigns across the model matrix actually used in production before
   claiming coverage for a model.

## Boundaries

- Campaigns need live agents and are NOT part of hermetic `run_all`; they are
  a separate lane whose RECEIPTS are committed, mirroring how live-runtime
  evidence stays separate from L3_HERMETIC admission everywhere else in this
  repository.
- A campaign receipt binds to the skill tree sha it evaluated; receipts for
  older trees are history, not current claims.

## Three-layer conformance (v2)

The repository's L0/L1/L2 architecture applies to campaigns, and the two
skill modes are layer bundles of one method, never two independent
approaches: procedure-rich = L0 only; domain-rich = L1(+L2); composed = all
three. A campaign must declare which layers each scenario exercises and may
claim only those. The 2026-08-31 pilot exercised L0 with an eval-owned L2
oracle and did not exercise L1 - recorded in its receipt. v2 scenarios add
an explicit in-fixture L1 artifact (capabilities, states, entry points) with
routing rubrics (consult before acting; refuse unmapped entry points) and
actor-side L2 rubrics (actor-persisted evidence, terminal-bound assertions).
