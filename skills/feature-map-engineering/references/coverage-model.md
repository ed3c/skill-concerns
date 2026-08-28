# Coverage model

## Universe

```text
C = actors × intents × entry points × variants × transitions × outcomes × environments
```

A direct Cartesian product is usually wasteful. Derive the required set using:

```text
behavioral equivalence
+ changed edges
+ trust/permission boundaries
+ persistence boundaries
+ platform/provider boundaries
+ known failure history
+ terminal impact
```

## Reconciliation

For each reachable terminal relevant to the changed feature:

- at least one `VERIFIED` journey reaches it; or
- one explicit blocked record retains the uncertainty.

A `PARTIALLY_VERIFIED` journey does not close the terminal by itself.

## Code and feature graphs

A large code diff may affect one behavioral edge. A one-line shared primitive change may affect many features. Determine coverage from ownership and behavior, not file count.

## Change-to-proof projection

```text
changed code
→ owned feature edges
→ risk-distinct journeys
→ observable assertions
→ proof or blocked record
```
