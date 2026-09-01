# Fixture system projection

## Directory and surface map

| Surface | Admitted writer | State |
|---|---|---|
| `pack/` | node-b | projection only |
| `spec/` | node-spec | canonical requirement |

No downstream projection may become an upstream authority. `[SRC-TREE, REPOSITORY_FACT, N]`

## Data and authority flow

```text
owner intent
  -> exact provider object
  -> candidate head and tree
  -> observed-state check
  -> merge and closure readback
  -> projection
```

The projection is the last node and never feeds back. `[SRC-BRIEF, OWNER_REQUIREMENT, N]` `[SRC-METHOD, METHOD_SOURCE, P]`

## Non-claims

The pack is not the specification, the provider, a scheduler, or an evidence
database, and it does not prove that an Agent read it. `[SRC-BRIEF, OWNER_REQUIREMENT, N]`
