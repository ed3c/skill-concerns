# Fixture implementation DAG projection

## Edge semantics

| Edge | Meaning | Closure authority |
|---|---|---|
| `S` | start-readiness | none |
| `C` | completion-readiness | the predecessor's own lane |
| `X` | external dependency | target-local readback |

Start-readiness never satisfies a completion edge. `[SRC-METHOD, METHOD_SOURCE, P]`

## Exact current completion graph

```text
node-a provider closed + marker landed
  C -> node-b ready and schedulable

node-c provider open + marker blocked
  X -> node-d blocked
```

Only exact markers appear as edges here. `[SRC-PROVIDER, R_REFERENCE, N]`

## Start-readiness graph

```text
node-e landed materialization
  S -> node-b bounded refresh
```

These start edges authorize no completion transition. `[SRC-TREE, REPOSITORY_FACT, N]`

## Convergence owners

| Concern | Exact owner | Current use |
|---|---|---|
| stable requirements | node-spec | canonical; node-b does not edit it |
| context compilation | node-b | the current pack writer |

Source for the whole table: `[SRC-PROVIDER, R_REFERENCE, N]`
