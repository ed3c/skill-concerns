# Assurance boundary

## What remains probabilistic

- discovering a useful capability;
- deciding whether it should be a Skill;
- naming actor-visible features;
- identifying stable domain boundaries;
- proposing a refactor;
- selecting risk-reduced journeys;
- interpreting ambiguous product intent;
- generating candidate domain adapters.

These steps can be reviewed and improved, but no prompt makes them physically deterministic.

## What is physically enforced

| Claim | Physical control |
|---|---|
| Agent instructions are bounded | complete `AGENTS.md` graph, depth/cycle/reachability checker |
| bundle anatomy is complete | registry + manifest + path checks |
| procedure and domain are separated | Skill kind, declared paths, forbidden-literal controls |
| routes are executable | scripts imported/executed by tests and suite runner |
| feature model is closed | state/transition/entry-point validation |
| terminal behavior is observable | reachable terminal oracle requirement |
| `VERIFIED` is evidence-backed | boundary-aware evidence validator |
| skipped path remains uncertainty | mandatory blocker, nearest path, residual uncertainty |
| changed feature has proof | changed-feature-to-journey reconciliation |
| negative controls remain present | eval case inventory and unit tests |
| receipt matches bytes | exact complete tree and contract SHA-256 set |
| evidence is not promoted | ordered evidence ceiling and explicit higher layers |

## Decision boundary

The Skill should guide decisions such as:

```text
behavioral documentation exists?
  yes → use it before implementation inference
  no  → create a provisional map and mark inference

path is externally observable?
  yes → require production-equivalent observable evidence

dependency unavailable?
  yes → block/skip explicitly; never substitute static inspection

multiple routes share changed behavior?
  yes → cover the shared contract and risk-distinct routes
```

The generic Skill does not prescribe which selector, endpoint, command, component, or provider exists. Those are domain contracts discovered or supplied by the consumer.
