# Evidence contract

## Evidence order

1. production-equivalent observable state;
2. persisted/reopened state;
3. external integration-boundary output;
4. subject-bound trace/telemetry;
5. integration test;
6. unit test;
7. static inspection.

## `VERIFIED`

A journey may be `VERIFIED` only when it includes observable evidence at one of:

```text
production-equivalent
external
persisted
```

If the feature requires persistence, at least one persisted item is mandatory.

## Lower-layer evidence

Trace, integration, unit, and static evidence may explain or localize behavior. They do not independently establish a `VERIFIED` user-facing terminal.

## Skips and blockers

A blocked path records:

```text
terminal or path
blocker type
unavailable dependency
details
nearest reachable path
residual uncertainty
```

A blocked record closes accounting, not behavior.

## Evidence ceiling

A hermetic fixture proves the validator and contract on that fixture. It does not prove a consumer domain, live Agent quality, or production behavior.
