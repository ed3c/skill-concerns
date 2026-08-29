---
name: control-noodle
description: >
  Control and verify the source-frozen Noodles Issue-to-reconcile lifecycle
  through explicit Feature and Code Maps. Use when a Noodles change must be
  mapped to required journeys, operated through supported control surfaces,
  or reported with exact proof and blockers.
---

# Control Noodle

Use this Skill for the bounded supervised lifecycle declared in [`domain/feature-map.json`](domain/feature-map.json). Do not treat it as authority to start, mutate, merge, or reconcile a live runtime unless the current task separately authorizes those actions and the target-local preconditions are physically present.

## Decision boundary

For each task:

1. bind the exact repository revision and actor-visible intent;
2. confirm `domain/composition.json` matches the admitted procedure and frozen domain subjects;
3. locate affected Code Map nodes from direct source readback;
4. compile those nodes through `domain/feature-code-map.json` into affected Feature Map transitions and required journeys;
5. reject unknown or unmapped code nodes instead of guessing ownership;
6. establish runtime, session, worktree, provider, and cleanup preconditions;
7. execute only supported domain-adapter operations;
8. collect observable evidence for the same exact subject;
9. reconcile the complete required-journey denominator;
10. report `VERIFIED`, `PARTIALLY_VERIFIED`, `BLOCKED`, or `NOT_VERIFIED` without evidence promotion.

## Knowledge placement

- Portable decision rules: [`references/portable-control-policy.md`](references/portable-control-policy.md).
- Domain control surface and constraints: [`references/control-surface.md`](references/control-surface.md).
- Behavioral topology: [`domain/feature-map.json`](domain/feature-map.json).
- Implementation topology: [`domain/code-map.json`](domain/code-map.json).
- Cross-graph ownership: [`domain/feature-code-map.json`](domain/feature-code-map.json).
- Concrete bindings: [`domain/domain-adapter.json`](domain/domain-adapter.json).

Read only the affected domain artifacts. The map is maintained memory, not permission to skip current source or runtime readback.

## Hard constraints

- Never infer feature ownership from a code path alone.
- Never silently update the frozen source commit.
- Never count an unavailable runtime or provider as verified.
- Never bypass the declared control boundary with direct state-file mutation.
- Never use a mutable upstream checkout path as an adapter dependency.
- Never claim live behavior from schemas, fixtures, unit tests, or hosted repository checks.

## Soft conventions

- Prefer exact subject identifiers over ambient current state.
- Prefer supported CLI/control operations over internal mutation.
- Prefer stable terminal polling and readback over sleeps.
- Prefer the smallest risk-complete journey set compiled from changed edges.

## Discoverable knowledge

Current order IDs, worktree paths, session IDs, PR heads, provider state, credentials, ports, and runtime availability are discovered per execution. Do not promote them into the maintained map from one observation.

## Hermetic authoring

Run the composed validator through the repository suite. Hermetic results establish contract behavior only. If a live dependency is absent, retain the nearest reachable path and residual uncertainty, then stop at the correct evidence ceiling.
