# AGENTS.md — context-closure-engineering

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — three-layer topology and what is frozen.
2. [`SKILL.md`](SKILL.md) — decision boundary and non-ownership.
3. [`references/portable-context-closure-policy.md`](references/portable-context-closure-policy.md) — L0, the eight laws.
4. [`domain/context-closure-topology.json`](domain/context-closure-topology.json) — L1 vocabularies, edge classes, negative ledger.
5. [`scripts/check_context_pack.py`](scripts/check_context_pack.py) — L2 execution + assertions.
6. [`references/consumer-adapter-contract.md`](references/consumer-adapter-contract.md) — what the consumer must supply.

## Stop laws

- A source enters the denominator once and never leaves it; unavailable bytes stay in it, marked absent.
- Start-readiness never satisfies a completion edge, and neither is a lifecycle marker.
- One durable value, one convergence owner. Two is a finding to surface, not a merge to perform.
- The pack is a dated projection: it never mutates what it describes and never backs a completion claim.
- A missing chain segment is named, not filled from a nearby object or from memory.
- A projection names the subject it was compiled over in one voice: a snapshot id that no longer matches its own baseline commit is stale, whatever the prose says.
- A candidate packet without a forbidden-promotion column is an instruction, not a proposal.
- Five of seven planted negatives are mechanized here; the two needing provider readback stay `NOT_MECHANIZED` with an owner. A hermetic PASS is not a consumer receipt.

## Completion

Run `python3 skills/context-closure-engineering/scripts/validate_context_closure_engineering.py`
and `python3 -m unittest discover -s skills/context-closure-engineering/tests`.
Report the count-tie result, the L2 selftest outcome, and the consumer-canary state.
