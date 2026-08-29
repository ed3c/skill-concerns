# control-noodle

Source-frozen composed Skill for controlling and verifying one bounded Noodles lifecycle without rediscovering its behavioral and implementation topology on every task.

## Three layers

```text
procedure kernel
  feature-map-engineering decision laws and proof semantics
        ↓ exact admitted subject
domain control pack
  Feature Map + Code Map + explicit mapping + adapter
        ↓ changed code nodes compile to required journeys
execution and proof
  deterministic validators + positive and planted-negative controls
```

The procedure dependency is content-bound in `domain/composition.json`. The domain subject is frozen to `ed3c/noodles@c820cacf92d4ad5ee033224d7a1d247f287642ed`.

## Bounded feature

```text
READY Issue
→ isolated worktree
→ execute handoff
→ provider landed
→ local machine reconciliation
```

This bundle does not own scheduling, worktree creation, provider landing, or live session state. It owns the decision and proof contract for selecting and reconciling those supported surfaces.

## Change → Feature → Proof compiler

```text
changed code nodes
        +
Code Map
        +
Feature↔Code mapping
        +
Feature Map
        ↓
affected transition IDs
        ↓
required journey IDs
        ↓
proof-plan denominator
```

The compiler is deliberately narrow. It does not infer feature ownership from repository layout, invent mappings, or operate the runtime.

## Parallelism boundary

Authoring and L3 verification use only content-bound fixtures in this repository. Active upstream work may advance Noodles after the frozen commit; that creates a new source subject but cannot mutate this admission subject. Live Noodles Issues #19 and #20 remain separate target-local evidence lanes.

## Evidence ceiling

The bundle reaches `L3_HERMETIC` when the exact maps, mapping, adapter, compiler, route, and mutations pass. It does not prove a live Noodle session, provider landing, consumer integration, or production behavior.
