# Noodles control surface

## Frozen subject

```text
repository  https://github.com/ed3c/noodles
commit      c820cacf92d4ad5ee033224d7a1d247f287642ed
```

Relevant upstream blobs:

| Path | Git blob |
|---|---|
| `AGENTS.md` | `7c441cf6119f3f42e2e30cf76fb45bf180f54345` |
| `README.md` | `c694e7e0e98bfd28361303bcdecf25d5bf6127b5` |
| `contracts/system-v1.md` | `2e8dd1e4f74de9555850344ffd4ec6f15fb396e2` |
| `.agents/skills/execute/SKILL.md` | `12e73fee4dc18fba8e235a31593f97db0fef4f2b` |
| `noodles.py` | `32e2480e8a2ca8130ebcfe7878981753224f3488` |
| `runtime_contract.py` | `b405b763098e44b3662eec3bfbcdfc2023be8dfa` |

## Supported domain bindings

- Handoff: `./noodles issue handoff REPO#N --pr N` → `execute_handoff` → `emit_blocking_handoff`.
- Provider observation: `provider_landed` reads the provider-landed subject.
- Reconciliation: `./noodles reconcile` → `reconcile_once` → Noodle snapshot/control acknowledgement and pending-review release.

## Preconditions

- exact Issue, repository, branch, PR head, and session subjects;
- target-local Noodle worktree authority;
- pinned runtime and provider policy;
- trusted provider workflow and protection readback;
- explicit cleanup/residue contract.

## Blockers

Unavailable runtime, missing session, stale head, absent provider receipt, mismatched Issue, or unreachable control API is `BLOCKED` or `NOT_VERIFIED`. The nearest reachable readback and residual uncertainty remain explicit.

## Active upstream lanes

- `ed3c/noodles#19` owns target-local verification-skill→physical-oracle admission.
- `ed3c/noodles#20` owns the first target-local executable feature-map canary.

This bundle does not complete or supersede either Issue.
