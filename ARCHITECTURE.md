# Architecture

## Stable plane boundary

`skill-concerns` owns one concern: **distribution admission for Agent Skills**.

It receives frozen proposals or source trees, hosts refactored bundles, executes deterministic admission gates, and publishes content-bound admitted artifacts. It does not own the upstream source repository, downstream consumer binding, secrets, live model/provider sessions, or production release state.

## Five concern layers

```text
L0 Procedure
  portable decision policy, invariants, stop conditions

L1 Domain knowledge
  product/repository vocabulary, features, commands, selectors, flags, constraints

L2 Execution
  drivers, polling, fixtures, assertions, test runners

L3 Behavioral model
  actor-visible feature graph, states, transitions, variants, observables

L4 Evidence
  exact subject, journeys, receipts, skips, denominator, evidence ceiling
```

A high-quality bundle makes these interfaces explicit. It may package several layers, but `skill.json` must identify which paths own each concern.

## Skill kinds

- `procedure-rich`: portable core; product/repository knowledge is supplied by a consumer adapter.
- `domain-rich`: concrete domain contract plus executable domain proof.
- `composed`: portable core and one or more declared domain adapters, each independently testable.

The kind is a machine policy, not a label. A `procedure-rich` Skill must have no declared domain paths and its portable paths are scanned for source-specific forbidden literals.

## Feature Map and Code Map

The two graphs are intentionally separate:

```text
Feature graph                         Code graph
actor intent                          entrypoint
→ entry point                         → module
→ state transition                    → service
→ observable outcome                  → persistence/RPC
```

A consumer may add a mapping between them. The portable Skill reasons about behavioral coverage without pretending repository structure is the feature structure.

## Promotion boundary

Probabilistic reasoning may create a candidate. Only deterministic checkers can create a valid admission subject. The receipt records what was measured and cannot grant a higher evidence layer than the executed suite.

## Three-document route

The Agent routing graph is deliberately smaller than the documentation graph:

```text
/AGENTS.md
→ /skills/AGENTS.md
→ /skills/<skill>/AGENTS.md
```

No nested local `AGENTS.md` files are allowed. References are selected after the final Agent contract and do not create further instruction inheritance.
