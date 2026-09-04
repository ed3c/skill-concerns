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
`duplicate-discovery`, `spec-first-lifecycle`, `shape-copying` and
`yielded-non-report`.

## The stations - where a pass is allowed to look

[`domain/observation-topology.json`](domain/observation-topology.json) is the
other half of the front-load: one row per station, each enumerating the inputs
the pass reads there, its access mode (read-only) and its feedback path (issues
and this bundle's ledger, nothing else). Two stations today - `wave-boundary`,
the one this bundle was admitted with, and `noodles-generation-close`, the
resident pass at a supervised generation's close-out.

The row ids are the run ledger's `subject` vocabulary, so the declining curve
slices by station and a record naming a station nobody declared reds instead of
inventing one. The generation-close row also names its
[runbook](domain/generation-close-runbook.md) step, whose completion IS the
appended run record: a close-out that carries no record for that generation is
incomplete in the next disposition rather than silently skipped. Its arrival is
tracked as a row in the ledger `skills/arrival-engineering` owns - the fixture
generation is what that row's receipts support today, and only a real
generation's record plus the matching run receipt move it.

A class whose falsification recipe is fully mechanical graduates into a consumer
CI gate through an ordinary atom and then leaves active sampling by the existing
lifecycle fields. The station's resident cost therefore trends toward the
judgement-needing residue, which is the same declining curve R7 already reads.

## The residual-sensor register

[`domain/residual-sensor-register.json`](domain/residual-sensor-register.json)
carries one row per known gap these gates cannot close, with four required
fields: the gap, the honest reason no mechanical form is available, the SENSOR
that would detect the gap being exploited, and the ESCALATION trigger with the
path a hit takes to become a filed tightening. A sensor is a readback this tree
can open holding a phrase that is really in it, so a sensor pointing at a duty
nobody wrote reds rather than reading as coverage. Gaps are findings, sensors
are oracles, triggers are class guards in waiting.

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
- Action: emit a record - catalogue class, subject at an exact sha256, an experiment block carrying the verbatim command sequence with expected and observed, a verdict with the ground it was produced from, and the both-directions status - and let the validator judge it. The block's grammar is fixed so it drops VERBATIM into an issue body's observer-demonstration section and survives that gate's stripping; the monitor manufactures admission-grade evidence and the dispatcher files with it. The verdict is COMPUTED from a filed adjudication, never assigned: a disposition names the subject sha256 it disposed of and its ground, `--adjudications` hands the pass its file, and a run reports which of the declared states it reached and how many of each.
- Why: an observer's silence is evidence only after it has demonstrated both directions, and a finding whose observed half is missing cannot show that it did - the blind probe reported a truthful zero for two waves because nothing in the record's shape demanded the other direction. The same separation is what a lane result needs one level up: a 117-byte payload reading "Still in progress. Yielding now" was counted as one of twelve completed results because the completion signal was trusted instead of judged. And a declaration of three verdicts in front of a producer that could write one is that shape aimed at this bundle's own field: hand triage disposed of the hits the instrument could not, off the record, because the record had nowhere to put a disposition that came back the other way.
- evidence: blind-observer, trusted-current-literal, yielded-non-report

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
- Action: read the run ledger's curve ONE STATION AT A TIME - known-class recurrence per wave over the records whose `subject` names that station - and deliver a finding to the dispatcher when it has not declined across three post-admission waves there. Blending stations reports a series no station produced, and lets a station that stopped gating hide inside a bigger one that did (ed3c/skill-concerns#130). `judge_gaps` and `duplicate_blocks` are derived views of the same record's `hits`, not two further series: a record whose columns disagree with the hits it carries was typed rather than produced, and reds. Read the RATE beside the series: `curve_rates()` divides each wave's recurrence by the artifacts that wave's passes actually swept, because a raw sum reads a bigger wave as a regression and wave size varies at every wave (ed3c/skill-concerns#167). The denominator comes from the producer's own walk and from no flag; a record taken before that field existed reads UNDENOMINATED and is never given a guessed one, and the decision this clause makes is still the raw series'. That is a finding about the architecture, not about the sampling, and fewer than three waves at a station is reported as not-yet-evidence rather than as a reassuring green.
- Why: a monitor that presumes its own effect is the observer whose silence nobody checked; the same defect class it exists to catch, one level up.
- evidence: duplicate-discovery

## R8. A resident station runs at the closed boundary and leaves a record

- Signal: a supervised generation is closing, or someone wants the monitor to watch one while it is still running.
- Action: run the pass only at the closed boundary, against artifacts read from a clone or a fixture, naming the station with `--subject`; persist the pass's own report with `--save-report` in the same invocation, and append the run record - live, or later from that artifact with `--from-report`. Treat the record as the step's completion. There is no mid-generation observation and no daemon-side invocation - the daemon never spawns a monitor - and a close-out with no record for its station is incomplete rather than clean. A pass that persisted no report and whose wave has landed cannot produce a record at all: it goes into [`domain/unpersistable-runs.json`](domain/unpersistable-runs.json) with its reason and WITHOUT its numbers, never typed into the ledger.
- Why: the zero-injection adjudication drew this boundary before the first run, and a resident duty whose completion is nobody's readback is a duty that gets skipped silently - which is the same absence-read-as-clean shape the blind-observer class exists to catch, one level up.
- evidence: zero-injection-boundary

## R9. Every gap the gates cannot close carries a sensor and a trigger

- Signal: about to write that something here is checked "only for shape", "not retroactively", or otherwise admit a limit in prose.
- Action: put the gap in the register with its four fields, and name the register row on the same line as the admission. If no sensor can be named, that is the finding: an admitted gap watched by nothing is an exemption with better manners, and a mechanical form that would only check that something is MENTIONED is refused as performative rather than counted as coverage.
- Why: a typed exit with no expiry, no pinned subject and no refusal is a waiver wearing a type - the class this bundle already catalogues - and an honest ceiling in a docstring is exactly that exit in prose form unless something is watching it.
- evidence: free-exit

## Diagnostics

The driver emits exactly these, and only these:

- `CATALOGUE_CLASS_HIT` - a catalogue class matched and the pass reached a verdict on it (R2/R4). The verdict is the finding's, not this line's: since ed3c/skill-concerns#152 a hit can come back confirmed, refuted or inconclusive, and a diagnostic asserting "confirmed it" was the mono-state instrument speaking.
- `ADJUDICATION_STALE` - a filed disposition bound to a subject sha256 this pass did not read; a triage is bound to the bytes it read (R4).
- `ADJUDICATION_UNGROUNDED` - a filed disposition with a missing field, a verdict outside the declared states, no ground, or two dispositions of one hit (R4).
- `VERDICT_PRODUCER_COLLAPSED` - the driver assigns a verdict as a literal, so the declared states have no producer again (R4).
- `NEIGHBOUR_ABSENCE_STALE` - a page in this bundle calls a neighbour unadmitted whose own admission receipt reads ADMITTED; an absence claim outlives what it was true about, and this one is settled by bytes in this repository (Non-claims).
- `CURVE_NOT_DECLINING` - three post-admission waves without a falling recurrence (R7).
- `SUBJECT_MUTATED` - the bundle digest moved during a reader-only pass; the report is untrusted (R3).
- `FINDING_MALFORMED` - a finding the validator's schema rejects (R4).
- `SIGNAL_CLASS_UNBOUNDED` - a signal citing a class outside the urgent list (R5).
- `SAVED_REPORT_UNGROUNDED` - a persisted report offered to `--from-report` whose own halves do not reconcile: a count that disagrees with the findings the same pass built from it, a finding the schema rejects, a read-only digest pair that never held, a blocked pass, or an instant that will not parse (R8).
- `RECORD_ALREADY_APPENDED` - a run offered to `--append-record` whose `run_id` the ledger already carries; the instant is the pass's, so a second row for it counts one measurement twice and doubles that wave's point (R8).
- `CATALOGUE_ENTRY_UNGROUNDED` - a class with no provenance, no runnable recipe, or no stock sweep (R1/R6).
- `CATALOGUE_GATE_REFERENCE_ABSENT` - a gated class with no gate to point at (R6).
- `CATALOGUE_CLASS_GATED_BUT_ACTIVE` - a class still sampled after its gate landed (R6).
- `DRIVER_SURFACE_FORBIDDEN` - a provider-mutating verb in the driver's own bytes (R3).
- `DEMONSTRATION_BLOCK_INCOMPLETE` - a rendered block the consumer's admission dry-run reads as empty (R4).
- `OBSERVATION_TARGET_UNGROUNDED` - a station with no enumerated inputs, no declared access or feedback, a runbook pointer that resolves to nothing, or a run record naming a station the topology does not carry (R8).
- `CEILING_WITHOUT_SENSOR` - a register row missing one of its four fields or citing a readback that does not exist, or a ceiling admitted in this bundle's prose with no register row named on the line (R9).
- `STATION_ARRIVAL_UNTIED` - a station whose records have outgrown the arrival row that tracks it, or an arrival row claiming a run the ledger never recorded (R8).
- `BUILD_CURE_UNAUTHORIZED` - a catalogue class folded in with no cure-authorization (R6). The rule and its decision live once in the repository's `scripts/cure_authorization.py`, which every BUILD carrier calls.

## Knowledge placement

Concern layers:

- L0 procedural - [`references/portable-falsification-kernel.md`](references/portable-falsification-kernel.md): one domain-free kernel per clause.
- L1 domain knowledge - [`domain/catalogue.json`](domain/catalogue.json) (the classes, their provenance and lifecycle), [`domain/run-ledger.json`](domain/run-ledger.json) (the append-only run records the curve reads, sliced by station), [`domain/observation-topology.json`](domain/observation-topology.json) (the stations and their access and feedback), [`domain/generation-close-runbook.md`](domain/generation-close-runbook.md) (the one close-out step this bundle owns), [`domain/persisted-reports/`](domain/persisted-reports/) (the producer's own report objects, so a record survives the land that destroys its bundle), [`domain/unpersistable-runs.json`](domain/unpersistable-runs.json) (the runs that cannot produce a record, refused with a reason and without numbers) and [`domain/residual-sensor-register.json`](domain/residual-sensor-register.json) (the gaps, their sensors and their triggers).
- L2 execution + assertions - [`scripts/shadow_driver.py`](scripts/shadow_driver.py) and [`scripts/validate_red_team.py`](scripts/validate_red_team.py), plus the fixtures under [`evals/fixtures/`](evals/fixtures/).

```sh
python3 scripts/shadow_driver.py --bundle <dir> --wave <name> --boundary <name>   # SHADOW: reader-only
python3 scripts/shadow_driver.py --bundle <dir> --subject <station> --append-record  # one station's record
python3 scripts/shadow_driver.py --bundle <dir> --class <class-id>                # one class's recipe
python3 scripts/shadow_driver.py --bundle <dir> --adjudications <file.json>       # dispositions -> verdicts
python3 scripts/shadow_driver.py --bundle <dir> --append-record                   # append one run record
python3 scripts/shadow_driver.py --bundle <dir> --save-report <file>              # persist the pass's own report
python3 scripts/shadow_driver.py --from-report <file> --append-record             # append after the wave landed
python3 scripts/shadow_driver.py --add-class <class.json>                         # BUILD: refuses an unadjudicated class
python3 scripts/validate_red_team.py [--selftest]
python3 scripts/gen_red_team_receipts.py                                                   # receipts.json's only author
```

## Non-claims

- No mid-flight intervention of any kind toward a worker or a subject. The escalation channel carries a signal to the dispatcher and nothing else.
- No filing. Nothing in this bundle creates, edits, comments on, closes or merges anything at the provider; `DRIVER_SURFACE_FORBIDDEN` is what keeps that true rather than the sentence that claims it, and it covers every script under `scripts/` in two forms - the verb scan over each file, and an import check that no module here can spawn a process or open a socket at all. The verb scan exempts exactly one file, its own owner `validate_red_team.py`, which necessarily carries the verbs it looks for; the import check is what covers that file, and it is the stronger of the two.
- No fourth judgment angle. `spatial-loop-grounded` issues clause verdicts over supervised conduct, `context-closure-engineering` compiles and checks one bounded context projection, `dynamic-workflow` classifies runtime liveness of dispatch lanes, and `shadow-architect` (ed3c/skill-concerns#75, admitted) carries the architecture angle. Those read and question; this one executes falsification. The differential is the verb.
- No ceremony and no wiring audit. `control-noodle` decides whether an atom's boundary was conducted correctly; `arrival-engineering` audits whether a declared capability is wired to anything, and owns the arrival vocabulary this bundle's station row is graded in. Stationing the pass at generation close put a red-team carrier inside both surfaces - a runbook step at a ceremony boundary, and a row in the arrival ledger - so the differential is named here instead of left to the reader: this bundle reads what they own and appends one row through their own producer, and grades neither.
- No autonomous catalogue growth and no gate replacement. A class enters only from an adjudicated verdict, and a class that gains a mechanical gate leaves active sampling rather than being re-checked by hand.
- No ownership of the consumer's issue-admission gate. `validate_red_team.completeness_reasons` is a declared MIRROR of that gate's shape, names the functions it mirrors and the checks it deliberately omits, and exists so the round-trip fixture can prove the block's grammar without this repository depending on the other one. Re-derived against `ed3c/noodles issue_contract.py@0c36bdf3` (ed3c/skill-concerns#137): the mirror now states WHICH reader grades each section, because since ed3c/noodles#317 the fence handling is two answers and not one — the demonstration section is graded fence-PRESERVING, everything else fence-stripping. The declared evidence-marker values join the two standing omissions as an input no body can supply, so the mirror takes them as an argument exactly as upstream does; passing none fails closed.
