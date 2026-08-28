# Feature schema

## Human semantics

```text
Feature
  actor-visible capability identity

Actor and intent
  who acts and what outcome they seek

Entry points
  supported routes and their initial states

States
  externally meaningful conditions

Transitions
  supported action edges

Variants
  roles, flags, platforms, protocols, providers, environments

Terminal outcomes
  success, cancel, error, empty, timeout, partial, blocked

Observables
  assertions tied to terminal state or transition

Persistence
  reload, reopen, restart, retry, or resume boundary
```

The machine topology is defined by `contracts/feature-map.schema.json`.

## Identity rule

A feature name should complete:

```text
<actor> can <achieve outcome>
```

Component, class, table, package, and service names may be implementation mappings but are weak feature identities.

## Reachability rule

Every entry point names a valid state. Every transition references valid states. A journey is an ordered path through reachable transitions. A reachable terminal needs an observable oracle even when the current environment later blocks execution.

## Observable rule

An oracle names what is externally inspectable, not merely which implementation path executed.
