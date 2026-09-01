# context-closure-engineering

Domain-rich Skill that compiles long, mixed source material into one bounded
projection - source denominator, surface and authority map, start/completion
DAG, closure matrix, traceability index, drift ledger - and then checks that
projection mechanically instead of trusting it.

Three skill-concern layers, one method:

- **L0 procedural**: `references/portable-context-closure-policy.md` - eight
  portable laws, domain-decoupled, one clause each.
- **L1 domain knowledge**: `domain/context-closure-topology.json` - the frozen
  source identity, pack roles, classification and authority vocabularies, edge
  classes, and the planted-negative ledger.
- **L2 execution + assertions**: `scripts/check_context_pack.py` - the checker
  and its selftest; `references/consumer-adapter-contract.md` is its human
  companion.

The source is frozen by blob identity, not by copy: the six upstream method
documents are pinned in `intake/context-closure-engineering/source-lock.json`
under `method_references`, so this tree carries none of their bytes and any
upstream edit is visible as a hash change.

Hillclimb gate: the validator is count-tied. The L1 topology declares how many
portable laws and how many planted negatives exist; dropping a law clause,
demoting a mechanized negative to prose, or naming a check the L2 checker does
not emit all fail closed. Five of seven planted negatives are mechanized; the
other two need an authenticated provider readback and are declared
`NOT_MECHANIZED` with their owner rather than quietly counted as passing.

Evidence ceiling `L3_HERMETIC`. The consumer canary is `NOT_EXERCISED`: a green
suite here is a producer receipt and says nothing about a live consumer.
