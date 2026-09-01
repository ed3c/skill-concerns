# Fixture molecular traceability index

## Trace shape

```text
source or owner problem
  -> bounded requirement
  -> exact provider object
  -> candidate head
  -> changed paths
  -> positive and planted-negative controls
  -> merge, closure, and reconciliation readback
```

Missing segments are `TRACEABILITY_GAP`; a nearby object or an Agent's memory
cannot fill them. `[SRC-BRIEF, OWNER_REQUIREMENT, N]` `[SRC-TREE, REPOSITORY_FACT, N]`

## Active molecular lanes

| Lane | Backward link | Forward link | Missing segment |
|---|---|---|---|
| pack compilation | `SRC-BRIEF` | node-b candidate head | merge readback |
| source refresh | `SRC-PAPER` | none | `TRACEABILITY_GAP` |

Each lane exposes its missing segment rather than closing it. `[SRC-PROVIDER, R_REFERENCE, N]`

## Known unavailable identity segments

- Raw owner-conversation transcript bytes. `[SRC-BRIEF, ABSENT, N]`
- Exact article title, URL, bytes, and hash. `[SRC-PAPER, EXTERNAL_CLAIM plus ABSENT, N]`
- Proof that a future Agent read every source. `[SRC-BRIEF, OWNER_REQUIREMENT, N]`
