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

## The judge's negative control

A judge that has never refused anything is a single arrival: every green it
has produced is unfalsified, not verified. The inventory therefore carries a
permanent `control: "negative"` case - a planted, deliberately violating
transcript (`evals/behavioral-campaigns/fixtures/`) with
`expected_verdict: "violated"` and the clauses it violates named.

- No actor is run for it. The planted transcript IS the input, handed to the
  judge in the same shape as a real actor run, in the same batch as the
  positive scenarios so the judge cannot tell them apart.
- Every campaign scores it. A wave whose judge returns PASS on it is void -
  the judge was not reading the call log, so its verdicts on the positive
  scenarios claim nothing.
- CI never judges. `validate_spatial_loop_grounded.py` asserts only the
  deterministic half: the case exists, declares `violated`, names real
  clauses, and its transcript bytes are present. Dropping or softening it
  fails closed (`negative-control-dropped`, `negative-verdict-softened`,
  `negative-transcript-missing`).

## The without-skill control arm

A single-armed campaign measures the actor+skill pair, never the skill. Every
green before 2026-09-01 was of that kind, and the pilot's own ledger entry
recorded the gap. The cure is a second arm: each disguised chore is run twice,
once in a workspace carrying the admitted clause bytes and once in a
byte-identical workspace carrying nothing. `ab_campaign.py stage` is the only
place the arms differ, and `diff -rq` between two staged workspaces prints
exactly one line.

- **The treatment is the admitted bytes.** The arm-with workspace receives the
  skill's own clause block, verbatim, under an innocuous filename; the excluded
  prefix and suffix are the parts that would tell the actor it is inside a
  skill evaluation. A test asserts every clause in `SKILL.md` is in the shipped
  slice, so a clause added outside it cannot silently stop being under test.
- **Blindness is exactly one invariant:** no judge input carries a
  harness-authored label of which arm produced it. The producer refuses to
  write judge inputs when any byte matches a hard label, it derives its token
  list from the runs directory rather than from the assignment, and a planted
  arm-leak fixture makes that refusal a CI-asserted test.
- **What blindness does NOT claim.** An actor holding the manual can cite it,
  and that citation survives into the judge input. That residual is a different
  quantity - actor-produced, not harness-authored - so it is counted per run
  and reported in the receipt as `treatment_traces` rather than asserted away.
  In the first campaign the judge flagged the trace itself, unprompted.
- **Two arrivals, not one.** Criteria decidable from bytes are ALSO decided
  mechanically from the call log and terminal state by the same script, and
  judge/oracle agreement lands in the receipt. A judge that stops reading the
  call log becomes visible instead of authoritative.
- **A tie is a result.** The scorer is deterministic and stdlib-only, and a tie
  is a finding about the skill, not a failure of the campaign. Reporting a null
  result is the whole point of having a control arm.

## Cross-wave judge ledger

`evals/behavioral-campaigns/ledger.json` carries one entry per judged wave -
`date`, `wave`, `judge_model`, `per_clause_summary`, `negative_control_verdict`,
`gaps`, `prompt_improvements`, `receipt_refs` - so per-clause verdicts form a
hillclimb gradient instead of isolated greens. Entries are hash-chained
(`prev_sha256` per entry, `head_sha256` for the tail): appending a wave never
touches prior bytes, while removing or rewriting one fails the validator
(`ledger-entry-removed`, `ledger-tail-rewritten`, `ledger-key-missing`).
Append through the producer `scripts/gen_ledger.py`; hand-editing the ledger
is laundering. `gen_ledger.py` also refuses to regenerate over a shortened or
rewritten `ENTRIES` list - the hash chain alone stays self-consistent even if
a prior wave's dict is dropped before re-running, so the producer diffs
against whatever is already on disk before it will write. A wave's `gaps`
and `prompt_improvements` are the next wave's input - that is what makes the
ledger a gradient rather than an archive.

`negative_control_verdict` records what the judge did with
`N-C3-C8-violating-actor` that wave: the case id plus its verdict, or an
explicit `NOT_RUN` with a reason for a wave that predates the control. This
is a presence check only (CI asserts the key is non-empty, same as the other
six) - a wave whose judge returned PASS/compliant on the negative control is
void per the rule above and must not be appended to the ledger at all; that
call is the operator's, not the validator's, matching the CI/runtime-judging
boundary this protocol already draws for the verdict itself.

A wave that genuinely finds no gap or no prompt improvement still records an
explicit sentinel (e.g. `["none identified this wave"]`), never an omitted or
empty key - omission fails the key-presence check, and an explicit negative
answer stays distinguishable from a wave that just forgot to look.
