---
name: context-closure-engineering
description: >
  Compile long owner conversations, provider objects, repository trees,
  articles, and monitor output into one bounded projection - source denominator,
  directory and authority map, start/completion DAG, closure matrix,
  traceability index, drift ledger - and check that projection mechanically. Use
  when a later Agent must recover the whole program without re-deriving it from
  the most recent prompt, and the recovery must not quietly promote prose into
  evidence or the projection into an actor.
---

# Context Closure Engineering

A context pack is a **dated projection over exact sources**, never current truth
and never an actor. It exists to defeat recent-prompt bias: the reader recovers
the source denominator, the global objective, current repository facts, the
unfinished closure obligations, the missing or duplicated ownership, and the
next leaf atoms - without treating any of that prose as verified.

The whole method reduces to eight laws in
[`references/portable-context-closure-policy.md`](references/portable-context-closure-policy.md).
They are portable; the file names, source ids, and vocabularies that instantiate
them are the consumer's, declared in
[`domain/context-closure-topology.json`](domain/context-closure-topology.json).

## Decision boundary

1. "What sources is this program made of, and which are unavailable?" -> freeze
   the denominator first. A source that cannot be read stays in the denominator
   marked absent; it never disappears from the accounting.
2. "Can this successor start, or can it finish?" -> two different edges. A start
   edge never satisfies a completion edge, and neither is a lifecycle marker.
3. "Who owns this durable value?" -> exactly one convergence owner. Two owners
   is a finding to surface, not a merge to perform later.
4. "Is this statement evidence?" -> no. Everything the pack emits is projection
   or pinned procedure. Only an actual run or an actual provider readback
   produces the classes above those, and neither happens here.
5. "This chain has a hole." -> name the hole. A nearby task, a commit message, a
   closed provider object, or an Agent's memory may not fill it.

## What this Skill does not own

Implementation, scheduling, workers, worktrees, merge, closure, or any provider
mutation. It does not become a second specification, requirement registry, issue
provider, closure database, or truth store. It does not read private chain of
thought. It consumes public monitor and orchestration output and emits
projections and candidate packets, which someone else may decide to act on.

The Shadow Architect, Tech Lead, and procedural-runtime methods stay where they
are: this bundle references those roles and never copies their procedures into a
mega-Skill.

## Executable contract

[`scripts/check_context_pack.py`](scripts/check_context_pack.py) judges a pack's
shape, source binding, denominator, edge classes, writer identity, and evidence
ceiling. It does not judge whether the writing is any good - that stays P-class
review, and pretending otherwise is the failure this bundle is built against.

```sh
python3 scripts/check_context_pack.py --pack <dir> [--bind ROLE=FILE] [--baseline prev.json]
python3 scripts/check_context_pack.py --selftest
```

Five of the seven planted negatives the method names are mechanized here. The
other two need an authenticated provider readback and are declared
`NOT_MECHANIZED` with their owner in the L1 topology, because a hermetic checker
comparing a frozen observation against itself cannot detect that the observation
went stale. That split is count-tied: the validator refuses when the seven rows,
the eight law clauses, or the checks a mechanized row names stop agreeing.

## Knowledge placement

These are the skill-concern layers (L0 procedural / L1 domain knowledge /
L2 execution + assertions): they answer where a piece of knowledge lives.

- L0 procedural - the eight portable laws: [`references/portable-context-closure-policy.md`](references/portable-context-closure-policy.md).
- L1 domain knowledge - frozen source identity, pack roles, vocabularies, edge classes, negative ledger: [`domain/context-closure-topology.json`](domain/context-closure-topology.json).
- L2 execution + assertions - [`scripts/check_context_pack.py`](scripts/check_context_pack.py) and its selftest.
- What the consumer must supply before any of this runs: [`references/consumer-adapter-contract.md`](references/consumer-adapter-contract.md).
