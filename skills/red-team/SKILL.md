---
name: red-team
description: >
  Run the judge's falsification method as a monitor at a stage boundary: match
  new artifacts (diffs, lane reports, receipts, filed issues) against a pinned
  catalogue of slop pattern classes, run each matched class's own falsification
  experiment, and hand back numbered findings shaped to drop into an issue
  body. Use at a wave or generation boundary, at wave close, or whenever a
  claim needs an experiment rather than a second reading. Reader-only against
  every subject; it files nothing.
---

# Red Team

The adversarial method that produced the strongest findings of the last five
waves lived only in dispatcher prompt text and scratchpad notes. This bundle is
that method as pinned bytes: a catalogue read at an exact commit, an experiment
per class, and a finding schema a validator owns.

Roles: **BUILD** is the only half that changes the catalogue - one adjudicated
class at a time, behind the repository's cure-authorization refusal, landing
through the PR ceremony. **SHADOW** is reader-only: it matches, falsifies, and
reports at severities S0 observe / S1 warn / S2 review, and never writes into
the subject it reads. A SHADOW pass whose subject digest moved refuses its own
report.

Front-loading is the whole point of the split. Rules front-loaded into a
working agent tax its generation; front-loaded into a monitor's clean context
they cost the worker nothing, because carrying the catalogue IS the monitor's
job.

## The catalogue - pinned bytes, front-loaded as the whole job

[`domain/catalogue.json`](domain/catalogue.json) is read at a commit, never
improvised. Each class carries:

- **provenance** - the filed receipt that grounded it and the cross-wave ledger
  entry that recorded it, so "which wave found this" is a readback;
- **a falsification recipe** - a runnable command sequence and the both-
  directions arm it must demonstrate, not a description of one;
- **lifecycle** - `active` or `gated`, the `gate_ref` when gated, and the
  `stock_sweep_ref` recording where that class's existing instances were
  dispositioned.

A gated class drops out of active sampling: a machine catches it now, and the
steady-state target of this bundle is its own silence. The classes are
`blind-observer`, `free-exit`, `trusted-current-literal`,
`duplicate-discovery`, `spec-first-lifecycle` and `shape-copying`.

## Clause form

Every clause is trigger-shaped: **Signal** (when to think of it) ->
**Action** (what to do) -> **Why** (the finding that proves it) ->
`evidence:` (ids resolved against [`receipts.json`](receipts.json)).

## R1. The catalogue is bytes at a commit, never rules improvised into a prompt

- Signal: about to review, judge, or monitor anything against "the patterns we keep seeing".
- Action: read the pinned catalogue first and sample from it; if a rule is not in those bytes at that commit, it is not a rule this pass enforces. A pattern remembered into a prompt is a pattern that will be remembered differently next time, and the drift is invisible because both readings sound right.
- Why: the judge method that produced the strongest findings of five waves lived in dispatcher prompt text and scratchpad notes - the same temp-dir island class the machine had just adjudicated for a body editor, rediscovered on the rules themselves.
- evidence: judge-method-strength

## R2. A catalogue hit is a hypothesis until its recipe runs

- Signal: a catalogue class matches an artifact and the match alone looks conclusive.
- Action: run that class's recipe against the exact subject and record expected and observed; report the class only with the experiment attached. A match is a reason to run the experiment, never a substitute for it - and a class whose recipe cannot be run is a class that cannot be reported.
- Why: the free-exit finding was not argued, it was executed on landed main: rewriting all nine producers in one receipts file to the typed exit and re-stamping through the skill's own producer still yielded a green sweep, which is what turned "this exit looks weak" into a measurement.
- evidence: free-exit

## R3. Reader-only against the subject; experiments run in throwaway clones

- Signal: an experiment would be easier to run against the live tree, the live branch, or the agent that is mid-flight.
- Action: read the subject and write nothing into it; run every experiment in a throwaway clone, and prove the read-only property by digesting the subject before and after rather than promising it. There is no mid-flight injection of any kind: the only real-time channel is one escalation signal to the dispatcher, who holds stop authority, and irreversible-class dangers belong to the architecture layer (branch protection, sandbox scope), not to monitor heroics.
- Why: the operator adjudication that admitted this organ drew that boundary before the first run, and the sibling observer bundle's own read-only guard is the shape it is tested with - a pass whose subject digest moved refuses its own report.
- evidence: zero-injection-boundary

## R4. A finding is a record with an experiment block, not prose with a number

- Signal: about to write "finding 3: X looks wrong" into a report.
- Action: emit a record - catalogue class, subject at an exact sha256, an experiment block carrying the verbatim command sequence with expected and observed, a verdict, and the both-directions status - and let the validator judge it. The block's grammar is fixed so it drops VERBATIM into an issue body's observer-demonstration section and survives that gate's stripping; the monitor manufactures admission-grade evidence and the dispatcher files with it.
- Why: an observer's silence is evidence only after it has demonstrated both directions, and a finding whose observed half is missing cannot show that it did - the blind probe reported a truthful zero for two waves because nothing in the record's shape demanded the other direction.
- evidence: blind-observer, trusted-current-literal

## R5. Escalation is one signal to the dispatcher, from a bounded list of classes

- Signal: something looks urgent enough to interrupt.
- Action: emit a signal - severity, catalogue class, subject, one line of reason, finding reference - and only for the enumerated urgent classes, `irreversible-action-in-progress` and `runaway-resource-burn`. The list lives in the contract; a signal citing anything outside it is a validator error rather than a louder signal. Signals carry no instructions and no patches.
- Why: an escalation channel with no bounded criteria becomes an escalation channel with no meaning, and one that carries a patch has quietly become the mid-flight intervention the boundary forbids.
- evidence: zero-injection-boundary

## R6. The catalogue grows only by adjudicated verdict and shrinks only by a landed gate

- Signal: a new pattern was detected, or an existing class now has a mechanical gate.
- Action: to grow, name the adjudicated verdict or ledger entry as a cure-authorization - detection is the beginning of an adjudication, never a licence to legislate. To shrink, move the class to `gated` with its `gate_ref` and its `stock_sweep_ref`; a gated class leaves active sampling, and an active class with a landed gate is a validator error in the other direction.
- Why: the copy-nearest-shape error this repository adjudicated is exactly what an auto-growing catalogue would automate, and a class left active after its gate landed spends the monitor's whole budget re-finding what a machine already refuses.
- evidence: shape-copying, spec-first-lifecycle

## R7. The instrument reports its own failure to bend the curve

- Signal: the monitor has been running for several waves and everything looks fine.
- Action: read the run ledger's curve - known-class recurrence per wave, judge gaps per wave, duplicate-fingerprint blocks per wave - and deliver a finding to the dispatcher when it has not declined across three post-admission waves. That is a finding about the architecture, not about the sampling, and fewer than three waves is reported as not-yet-evidence rather than as a reassuring green.
- Why: a monitor that presumes its own effect is the observer whose silence nobody checked; the same defect class it exists to catch, one level up.
- evidence: duplicate-discovery

## Diagnostics

The driver emits exactly these, and only these:

- `CATALOGUE_CLASS_HIT` - a catalogue class matched and its experiment confirmed it (R2).
- `CURVE_NOT_DECLINING` - three post-admission waves without a falling recurrence (R7).
- `SUBJECT_MUTATED` - the bundle digest moved during a reader-only pass; the report is untrusted (R3).
- `FINDING_MALFORMED` - a finding the validator's schema rejects (R4).
- `SIGNAL_CLASS_UNBOUNDED` - a signal citing a class outside the urgent list (R5).
- `CATALOGUE_ENTRY_UNGROUNDED` - a class with no provenance, no runnable recipe, or no stock sweep (R1/R6).
- `CATALOGUE_GATE_REFERENCE_ABSENT` - a gated class with no gate to point at (R6).
- `CATALOGUE_CLASS_GATED_BUT_ACTIVE` - a class still sampled after its gate landed (R6).
- `DRIVER_SURFACE_FORBIDDEN` - a provider-mutating verb in the driver's own bytes (R3).
- `DEMONSTRATION_BLOCK_INCOMPLETE` - a rendered block the consumer's admission dry-run reads as empty (R4).
- `BUILD_CURE_UNAUTHORIZED` - a catalogue class folded in with no cure-authorization (R6). The rule and its decision live once in the repository's `scripts/cure_authorization.py`, which every BUILD carrier calls.

## Knowledge placement

Concern layers:

- L0 procedural - [`references/portable-falsification-kernel.md`](references/portable-falsification-kernel.md): one domain-free kernel per clause.
- L1 domain knowledge - [`domain/catalogue.json`](domain/catalogue.json) (the classes, their provenance and lifecycle) and [`domain/run-ledger.json`](domain/run-ledger.json) (the append-only run records the curve reads).
- L2 execution + assertions - [`scripts/shadow_driver.py`](scripts/shadow_driver.py) and [`scripts/validate_red_team.py`](scripts/validate_red_team.py), plus the fixtures under [`evals/fixtures/`](evals/fixtures/).

```sh
python3 scripts/shadow_driver.py --bundle <dir> --wave <name> --boundary <name>   # SHADOW: reader-only
python3 scripts/shadow_driver.py --bundle <dir> --append-record                   # append one run record
python3 scripts/shadow_driver.py --add-class <class.json>                         # BUILD: refuses an unadjudicated class
python3 scripts/validate_red_team.py [--selftest]
python3 scripts/gen_receipts.py                                                   # receipts.json's only author
```

## Non-claims

- No mid-flight intervention of any kind toward a worker or a subject. The escalation channel carries a signal to the dispatcher and nothing else.
- No filing. The driver never creates, edits, comments on, closes or merges anything at the provider; `DRIVER_SURFACE_FORBIDDEN` is the scan that keeps that true rather than the sentence that claims it.
- No fourth judgment angle. `spatial-loop-grounded` issues clause verdicts over supervised conduct, `context-closure-engineering` compiles and checks one bounded context projection, `dynamic-workflow` classifies runtime liveness of dispatch lanes, and the unadmitted `shadow-architect` (ed3c/skill-concerns#75) will carry the architecture angle. Those read and question; this one executes falsification. The differential is the verb.
- No autonomous catalogue growth and no gate replacement. A class enters only from an adjudicated verdict, and a class that gains a mechanical gate leaves active sampling rather than being re-checked by hand.
- No ownership of the consumer's issue-admission gate. `validate_red_team.completeness_reasons` is a declared MIRROR of that gate's shape, names the functions it mirrors and the two checks it deliberately omits, and exists so the round-trip fixture can prove the block's grammar without this repository depending on the other one.
