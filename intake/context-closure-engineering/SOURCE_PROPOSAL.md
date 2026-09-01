# Source proposal — context-closure-engineering

Owner design brief for `ed3c/skill-concerns#9`. This document is the frozen
proposal; the method bytes it refactors are frozen separately by blob identity
in `source-lock.json` under `method_references`, so this repository carries a
pointer rather than a copy.

## Exact method source

The method exists as six documents materialized by the consumer canary
`ed3c/noodles#117`, at commit `2f926297ab66ae62784bf3f5d7cd3089bc890f1c`, under
`docs/design/context-closure/`: `README.md`, `SYSTEM.md`, `DAG.md`,
`CLOSURE.md`, `TRACEABILITY.md`, `DRIFT.md`. Their blob hashes are the locked
identity. That directory is `N-class` in its own repository: it gates nothing
there, and reading it here grants nothing either.

`ed3c/skill-concerns#9` also names `ed3c/skills-shared@52b29b38...` as a method
reference for the Shadow Architect, Tech Lead, and procedural-runtime roles.
Those roles are referenced by name in the bundle and their procedures are not
copied. The bundle composes them; it does not absorb them.

## What is admitted

A `domain-rich` bundle in three layers:

- **L0 procedural** — eight portable laws, one clause each: denominator,
  anchoring, non-promotion, edge split, single convergence owner, traceability
  gap, non-mutation, external claim.
- **L1 domain knowledge** — the frozen source identity, the six pack roles and
  their default file names, the classification and authority vocabularies, the
  five edge classes, the planted-negative ledger, and the consumer-canary state.
- **L2 execution + assertions** — a checker over a pack directory, with a
  selftest that replays every mechanized planted negative.

## Deterministic controls

The method's own drift ledger lists seven planted negatives and records that
none of them was mechanized. Five are mechanized here:

| Probe | Mechanized as |
|---|---|
| remove one denominator source | `SOURCE_UNDECLARED` |
| replace a completion edge with a start edge | `EDGE_CLASS_COLLAPSE` |
| two active writers for one durable value | `DUPLICATE_WRITER` |
| cite the pack as completion evidence | `EVIDENCE_PROMOTION` |
| delete the absent article/PDF row | `DENOMINATOR_SHRINK` |

Two are not, and are declared `NOT_MECHANIZED` with their owner: a predecessor
read as landed from merge ancestry while its provider marker disagrees, and an
open change with green candidate checks treated as ready while the trusted check
fails. Both need an authenticated readback of current provider state; a hermetic
checker can only compare a frozen observation against itself, which is exactly
the failure they probe.

## Evidence ceiling

`L3_HERMETIC`. Consumer integration at `ed3c/noodles#117` is a separate receipt
this repository does not hold: `consumer_canary.state` is `NOT_EXERCISED`, and
the validator refuses any stronger value from this tree.

## Non-claims

This bundle does not replace the Shadow Architect, Tech Lead, or
procedural-runtime methods, or the already-admitted local bundles it may compose
with. It does not make a long context complete because six files exist, does not
guarantee an Agent reads or obeys the context, does not create a second
specification, registry, closure database, scheduler, worktree manager, or merge
authority, and does not treat conversation, article, PDF, or model consensus as
verified truth.
