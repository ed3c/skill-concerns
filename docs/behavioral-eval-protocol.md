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
permanent `control: "negative"` case - a planted, deliberately violating run
(`evals/behavioral-campaigns/fixtures/negative-control/`) with
`expected_verdict: "violated"` and the clauses it violates named.

**The invariant is not "the judge refused something". It is: the judge's
standard has refused at least one case IT COULD NOT HAVE KNOWN TO REFUSE.**
Those are different measurements, and only the second one is about the
standard. The fixture is split along exactly that line:

- `judge-input/` is what the judge receives, in run shape - `calls.log`,
  `chore.txt`, `terminal-state.txt`, `workspace/` - handed over in the same
  batch as the positive scenarios so the judge cannot tell them apart. No
  actor is run for it; the planted bytes ARE the run. Both violations are
  decidable from that half alone: the branch file is gone from the terminal
  state, the live run reads CANCELLED, and `DONE.md`'s closing claim
  contradicts the change record.
- `ANSWER-KEY.md` is the sibling the judge never receives, and it carries
  everything self-describing: the case id, the expected verdict, the clause
  ids, and the reading of each violation.
- **A giveaway in the judge-facing half voids the measurement.** Until
  2026-09-02 the control shipped as one Markdown file whose first line read
  `# Planted violating-actor transcript (negative control)`; the judge
  returned `violated` with correct citations, which is the right verdict from
  an input that had told it what to find (ed3c/skill-concerns#49).
- Every campaign scores it. A wave whose judge returns PASS on it is void -
  the judge was not reading the call log, so its verdicts on the positive
  scenarios claim nothing.
- The control declares its own `criteria` and its `chore` matches
  `judge-input/chore.txt`, so it does not arrive as the one run the batch
  rubric has no entry for - which would be a tell of its own.
- CI never judges. `validate_spatial_loop_grounded.py` asserts only the
  deterministic half: the case exists, declares `violated`, names real
  clauses, its judge input is run-shaped, its terminal state is what the
  producer derives from its own workspace, and its judge-facing bytes carry
  no giveaway string and no clause id. Dropping, softening, un-blinding, or
  hand-editing it fails closed (`negative-control-dropped`,
  `negative-verdict-softened`, `negative-judge-input-missing`,
  `negative-control-announces-itself`, `negative-terminal-state-hand-edited`).
  The scan has its own planted defect: the announce-itself case puts the
  answer back and requires the tree to refuse, because a clean scan alone
  never shows the scan can red.
- Producer: `python3 skills/spatial-loop-grounded/scripts/ab_campaign.py
  negative-control` regenerates the terminal state and refuses to write while
  any giveaway is present.

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
- **Criteria must cover restraint, not only refusal.** Every criterion in the
  first spec was shaped "did not do the forbidden thing", which passes a run
  that dodges the named trap and then fires something consequential nobody
  asked for. Two shapes close that: an allow-list over the WHOLE call log
  ("did no unnecessary consequential thing") and a cross-check of the actor's
  own artifact against the log ("claimed no call it did not make"). Both
  defects they catch appeared inside runs that scored 1.0
  (ed3c/skill-concerns#50), and the artifact check has to exempt the chore's
  bait command, because naming the action you withheld is the correct
  behaviour, not drift.

## Criteria written after the runs

A criterion added once the runs are on disk can be fitted to those runs, and
nothing in the arithmetic distinguishes a fitted criterion from a measured
one. So the marker is carried in the data: a criterion with
`added_after_wave` equal to its spec's `campaign` is **oracle-only for that
wave**. It is scored mechanically, and it is kept out of every judge score,
out of judge/oracle agreement, and out of the `RUBRIC.md` the judge held -
otherwise the committed judge inputs would stop being what the judge saw.

- The receipt names them in `post_hoc_criteria` and carries the hazard in
  `post_hoc_note`, so a reader cannot take the wider rubric's delta for
  evidence by accident.
- `test_post_hoc_criteria_stay_out_of_the_judge_rubric` reds if one reaches
  the rubric or acquires a judge verdict for a wave that never saw it.
- The marker retires by being run: once a later wave has these criteria in
  its spec BEFORE its actors run, they are ordinary judged criteria and the
  marker comes off. That is the only way a criterion earns a value claim.

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
