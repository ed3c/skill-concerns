# Consumer adapter contract

The portable laws and the executable checker are useless without a consumer.
This document names exactly what the consumer owns, so that an absent consumer
surface stays absent instead of being simulated here.

## The consumer supplies

| Surface | Why it cannot live here |
|---|---|
| Repository and provider APIs, and the credential to reach them | This bundle holds none, by design. A distribution plane that carries a provider credential is a second actor. |
| The output root the pack is written to | The pack's directory is the consumer's write boundary, and its own contract decides what may be written there. |
| Exact object and state schemas | Marker names, lifecycle values, and dependency syntax belong to whoever owns the provider objects. |
| Directory vocabulary and ownership surfaces | The surface map is a fact about one repository. |
| Requirement and feature identifiers | Only the consumer knows what its own requirements are called. |
| Target-specific tests, oracles, and evidence lanes | The evidence classes above projection are produced by runs, not by documents. |
| Access to private conversations, images, and PDFs | Unavailable bytes stay absent in the denominator; this bundle never fabricates them. |
| Provider mutation authority, if separately admitted | Never granted by reading this Skill. |

## File-name binding

The six pack roles are `README`, `SYSTEM`, `DAG`, `CLOSURE`, `TRACEABILITY`, and
`DRIFT`. Their file names are consumer bindings, not portable constants: the L1
topology carries defaults and `--bind ROLE=FILE` overrides any of them. A
consumer that renames a file changes one argument, not the method.

## Baseline binding

`--baseline` takes the previous pack's denominator. Without it the checker can
still see an undeclared source, but it cannot see a denominator that shrank -
the failure where a source quietly leaves the accounting and the omission looks
like an edit. A consumer that never passes a baseline has that check absent, not
passing.

## The two provider-owned negatives

Two planted negatives from the method are declared `NOT_MECHANIZED` in the L1
topology and belong to the consumer:

- a predecessor read as landed from merge ancestry while its provider marker
  disagrees;
- an open change with green candidate checks treated as ready while the trusted
  check is failing.

Both need an authenticated readback of current provider state. A hermetic
checker can only compare the pack against itself, and a frozen observation
cannot detect that it went stale. The consumer that owns the provider lane owns
these two, and until it exercises them they stay `NOT_EXERCISED`, never passing.
