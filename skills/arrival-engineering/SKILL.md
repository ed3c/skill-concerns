---
name: arrival-engineering
description: >
  Audit the capability wiring graph at rest: for each declared capability, who
  consumes it, through which bound exit, and at which measured arrival level -
  and does every claim match? Use when a capability, verb, pin, or cross-repo
  pointer has been declared and nobody has proved a consumer reaches it, or
  when a claim ("available", "recorded in X", "in use") needs reducing to the
  arrival its receipts actually support. Owns the DECLARED / EXERCISED /
  PRODUCTION arrival vocabulary.
---

# Arrival Engineering

A declared capability is not a used one. This Skill audits the graph between
declaration and consumption, and records, per capability, the highest arrival
its receipts support. Its subject is wiring at rest, not runtime liveness and
not a compiled context projection - see [Non-claims](#non-claims).

Roles: **BUILD** is the only half with a write verb - it appends topology rows
and regenerates receipts under this Skill's own directory and nowhere else, and
lands through the repository's PR ceremony. **SHADOW** is reader-only: it runs
the island audit and reports findings at severities S0 observe / S1 warn /
S2 review, never patching what it finds. A SHADOW pass that mutated its subject
refuses its own report.

## The arrival ledger - DECLARED / EXERCISED / PRODUCTION

This Skill is the single owner of this vocabulary. Other bundles may cite these
levels; none may redefine them.

- **DECLARED** - the bytes exist and a validator or gate can see them.
  Proves possibility only.
- **EXERCISED** - a fixture, selftest, or test ran the capability on
  synthetic input. Sandbox arrival.
- **PRODUCTION** - a session, cycle, or cadence receipt from a real run
  names it.

The levels do not imply each other. A capability's recorded level is not a
judgement but a derivation: it must **equal** the highest level an actual
receipt supports (`bytes` -> DECLARED, `exercise` -> EXERCISED, `run` ->
PRODUCTION). Above reds `CLAIM_ABOVE_ARRIVAL`; below reds
`CLAIM_BELOW_ARRIVAL`, because a row that rises only when an author remembers
to raise it is the stale list this ledger exists to kill.

These names are words, not numbers, on purpose. Two other axes in this
repository count from L0 - the bundle-anatomy concern layers, and the
`L0_SOURCE_FREEZE .. L5` evidence ceiling that `registry.json` and the
admission receipt own. An earlier draft numbered arrival too and carried a
paragraph asking the reader to keep three L-numberings apart. This axis was
the newest of the three and had no consumers, so it was the one that moved:
naming it removes the collision instead of documenting it.

## Clause form

Every clause is trigger-shaped: **Signal** (when to think of it) ->
**Action** (what to do) -> **Why** (the finding that proves it) ->
`evidence:` (ids resolved against [`receipts.json`](receipts.json)).

## A1. Audit five surfaces, or the audit itself only proves declaration

- Signal: about to answer "is this consumed?" for a script, verb, module, artifact, or pin.
- Action: scan all five consumption surfaces before answering - `imports` (production code that names it), `value_flow` (committed artifacts read back by something), `ci` (a gate or workflow whose argv reaches it), `adapter` (an installed entrypoint, wrapper, or scheduler job), `cli_text` (a documented invocation an agent would actually run). Report the surface set, not a verdict; an audit that read only the import graph has proved declaration, not arrival, and is itself a DECLARED-level claim about a question that was never about declaration.
- Why: the trigger island had an offline-provable core and zero runtime consumers, and every earlier reading of it "looked wired" because only one surface was ever consulted - the verb was absent, the execution skill silent, and the actual navigation was unguided text search.
- evidence: five-surface-audit, consumer-less-core

## A2. Availability is not use: an unbound verb is a planned island

- Signal: a capability is being delivered as a verb, flag, endpoint, or script that a consumer "can call".
- Action: refuse the delivery until the verb is bound to an exit the consumer already traverses, and until the receipt that certifies the consumer's work is inadmissible without it. "May remember to call" is the island being planned rather than found; the cure is shared-exit binding plus receipt admissibility, not documentation.
- Why: a runtime-surface draft shipped a verb a cook could remember to call; the amendment bound the capability to the checkout ceremony every cook already runs and made cross-repo receipts inadmissible without it, converting a planned island into a traversed exit.
- evidence: planned-island, shared-exit-cure

## A3. A claim above its measured arrival is a finding

- Signal: writing or reading "available", "in use", "wired", "verified", "in production" about a capability.
- Action: reduce the claim to the highest arrival an actual receipt supports and record it in the topology with that receipt's path. Level upgrades happen only by receipt readback - never by a second reading of the same bytes, never by time passing, never because the capability plainly ought to work by now.
- Why: five admitted bundles carry a production cadence receipt that names their checks; the sixth was admitted after that run and has never been in one, so an unqualified "all admitted Skills are swept nightly" is a claim one level above what the bytes support for that bundle.
- evidence: arrival-ledger, cadence-run-denominator

## A4. Every "recorded in X" is checked against X's bytes

- Signal: a header, README, receipt, or comment says a fact is mirrored, pinned, locked, or recorded somewhere else.
- Action: open X and grep for the exact value before believing or repeating the claim. A documented pin whose target does not carry it is worse than no pin: it retires the reader's suspicion while retiring nothing else.
- Why: a module header claimed its tool pins were mirrored in a lock file; live readback showed the lock had no such entries, and the claim had been read past repeatedly because reading it felt like checking it.
- evidence: false-documented-pin

## A5. Cross-repo pointers are re-verified against live trees

- Signal: an interface, topology, or capability row names something owned by another repository, or an upstream carrier is adjudicated retired.
- Action: resolve every cross-repo pointer against the live tree or provider on a cadence, and treat upstream retirement as a maintain-on-event trigger for every row that points at the retired carrier. Publish unresolvable and unreadable as different states - absence is a finding, unreachability is a prerequisite.
- Why: a code-intel topology named probe interfaces whose carrier had been adjudicated retired upstream; nothing in the pointing repository re-read the pointer, so the rows stayed green while their target stopped existing.
- evidence: dangling-pointer, retired-carrier

## A6. Closure is by pointer to its owner, never by restatement

- Signal: a finding is about to be reported, recommended, or "noted".
- Action: terminate it in a durable home some process re-reads - an issue number, a `path:line` an existing validator or test already reads, or the dispatcher's ledger - and refuse to recommend a file that does not exist or a key nothing sweeps. The closure method itself is owned by `context-closure-engineering`: LAW-TRACE-GAP (name the hole; nothing nearby may fill it) and LAW-NO-PROMOTION (a projection never becomes evidence) live in
  [`../context-closure-engineering/references/portable-context-closure-policy.md`](../context-closure-engineering/references/portable-context-closure-policy.md)
  and are not restated here. This clause adds only the arrival-specific refusals: a destination that does not exist, and an ANSWERED with no mechanical reader.
- Why: the one tested copy of a law belongs in its owner; a restated second copy drifts from the copy that is actually exercised, and the restatement is the drift the split exists to prevent.
- evidence: closure-by-pointer

## Diagnostics

The island audit driver emits exactly these, and only these:

- `CONSUMER_ABSENT` - no surface names the capability's exit (A1).
- `VERB_WITHOUT_CONSUMER` - an exit exists with no bound exit a consumer traverses (A2).
- `CLAIM_ABOVE_ARRIVAL` - the recorded level exceeds what the receipts support (A3).
- `CLAIM_BELOW_ARRIVAL` - the receipts already support more than the recorded level (A3).
- `DOCUMENTED_PIN_FALSE` - a "recorded in X" whose value is absent from X (A4).
- `POINTER_DANGLING` - a cross-repo or cross-tree pointer that does not resolve (A5).
- `TOPOLOGY_ROW_WITHOUT_RECEIPT` - an aspirational row, refused at append (A3/A6).

## Knowledge placement

Concern layers, not arrival levels:

- L0 procedural - [`references/portable-arrival-kernel.md`](references/portable-arrival-kernel.md): one domain-free kernel per clause.
- L1 domain knowledge - [`domain/capability-topology.json`](domain/capability-topology.json): the audited capability rows and their receipts.
- L2 execution + assertions - [`scripts/validate_arrival_engineering.py`](scripts/validate_arrival_engineering.py) and [`scripts/audit_islands.py`](scripts/audit_islands.py), each with a `--selftest`, plus the planted fixtures under [`evals/fixtures/`](evals/fixtures/).

```sh
python3 scripts/audit_islands.py --tree <dir> --topology <file>   # SHADOW: read-only
python3 scripts/audit_islands.py --selftest
python3 scripts/audit_islands.py --append-row <row.json>          # BUILD: refuses a receipt-less row
python3 scripts/validate_arrival_engineering.py [--selftest]
python3 scripts/gen_receipts.py                                   # BUILD: receipts.json's only author
```

## Non-claims

- No new scheduler, daemon, or service. SHADOW rides the maintain cadence that already exists by putting its provider refs in `receipts.json`, which that sweep already globs; maintain-on-event is a hand trigger.
- No runtime liveness. Session and workflow liveness stay with `dynamic-workflow`; this Skill audits wiring and arrival and never decides whether something has stalled.
- No method-stack ownership. `control-code-intel` keeps the code-intel stack; this Skill only records that stack's arrival levels.
- No context projection. `context-closure-engineering` owns compiled context packs and the closure laws A6 points at.
- No cross-repo writes in either mode. BUILD's entire write surface is this directory on a branch in its own clone; the audit driver never writes to the tree it audits.
- No auto-cure and no aspirational rows: BUILD proposes, the machine ceremony lands, and a row without a receipt is refused at append rather than parked as a to-do.
