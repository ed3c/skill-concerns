# Source proposal — control-noodle

Owner-authorized composed Skill canary for Issue #4.

## Exact domain subject

```text
repository  https://github.com/ed3c/noodles
commit      c820cacf92d4ad5ee033224d7a1d247f287642ed
```

Selected upstream method files and Git blobs:

```text
AGENTS.md                         7c441cf6119f3f42e2e30cf76fb45bf180f54345
README.md                         c694e7e0e98bfd28361303bcdecf25d5bf6127b5
contracts/system-v1.md            2e8dd1e4f74de9555850344ffd4ec6f15fb396e2
.agents/skills/execute/SKILL.md    12e73fee4dc18fba8e235a31593f97db0fef4f2b
noodles.py                         32e2480e8a2ca8130ebcfe7878981753224f3488
runtime_contract.py                b405b763098e44b3662eec3bfbcdfc2023be8dfa
```

The repository and local checkout were both observed at the exact commit before authoring. These files establish the supported command surface, supervised state machine, authority classes, execution handoff, provider readback, reconciliation, and non-claims.

## Selected vertical slice

```text
READY Issue
→ isolated worktree
→ execute handoff / awaiting_land
→ exact-head provider landing
→ local Noodle reconciliation
```

## Concern split

- Procedure: reuse the exact admitted `feature-map-engineering` subject.
- Domain: Feature Map, Code Map, explicit mapping, adapter, commands, subjects, boundaries, and blockers.
- Execution: generic composed-contract validator and change-to-journey compiler.
- Evidence: hermetic fixtures, positive controls, planted mutations, admission receipt, and explicit L4/L5 non-claims.

## Parallelism and source drift

Active upstream Issue #37 has its own managed worktree and may advance `ed3c/noodles/main`. Upstream Issues #19 and #20 own target-local verification and feature-map canaries. This candidate writes only `skill-concerns`; it does not operate any Noodle runtime or mutate upstream state. A later upstream commit is a new source subject and cannot silently alter this candidate.
