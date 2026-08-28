---
name: feature-map-engineering
description: >
  Discover, model, and verify software through actor-visible FeatureMap IR.
  Use when implementing, debugging, reviewing, or validating UI, API, CLI,
  workflow, service, or agent behavior while separating portable procedure,
  repository-specific domain knowledge, execution mechanics, and proof.
---

# Feature Map Engineering

Use this Skill to reason about a system through externally meaningful capabilities rather than code structure alone.

A feature map states what an actor can achieve, how the capability is reached, which state transitions and variants matter, and what observable evidence proves each outcome.

Do not assume the repository tree is the feature tree.

## Core contract

For each task:

1. identify the actor-visible capability and intent;
2. locate or construct its feature map;
3. map the change to affected feature edges;
4. derive the smallest risk-complete journey set;
5. execute production-equivalent supported paths;
6. observe externally meaningful state;
7. reconcile every reachable terminal and explicit blocked path;
8. report the exact evidence state;
9. update the map only when the behavioral contract changed.

Implementation completion is not feature completion.

## Separation of concerns

### Portable procedure

This Skill owns:

- discovery order;
- feature identity;
- feature decomposition;
- coverage reasoning;
- evidence hierarchy;
- skip semantics;
- decision boundaries;
- completion and stop rules.

### Domain adapter

The consumer repository owns:

- domain vocabulary;
- feature inventory;
- commands and protocols;
- semantic selectors;
- endpoints;
- feature flags;
- fixtures;
- runtime setup;
- environment constraints;
- product-specific assertions.

### Execution

Drivers and code own:

- browser, API, CLI, database, device, workflow, or agent actions;
- polling and synchronization;
- fixture creation;
- trace collection;
- concrete assertions;
- durable proof artifacts.

### Behavioral model

FeatureMap IR owns:

- actor and intent;
- entry points;
- states;
- transitions;
- variants;
- reachable terminal outcomes;
- observable contracts;
- persistence requirements.

A generic procedure must not hard-code one domain's driver, selector, command, component, endpoint, or architecture.

## Locate or construct the map

Look first for maintained behavioral sources:

- feature documentation;
- user journeys;
- acceptance tests;
- public API or CLI documentation;
- route and command definitions;
- workflow or state-machine contracts;
- integration tests;
- runtime observations.

Prefer maintained behavioral documentation over reconstructing behavior from implementation code.

When no map exists, construct a provisional map from evidence. Mark inference as provisional until runtime observation confirms it.

Runtime reality wins when documentation and observed behavior conflict. Repair the stale map rather than forcing reality to match prose.

## Feature identity

Define a feature from the actor's point of view:

```text
actor can achieve outcome
```

Prefer:

- user can filter jobs by location;
- operator can retry a failed workflow;
- API client can rotate a credential;
- agent can resume a suspended run.

Avoid using implementation objects as the behavioral boundary:

- FilterPanel component;
- RetryService;
- CredentialController;
- RunStateReducer.

Implementation objects may realize a feature but do not define its observable contract.

## Feature decomposition

For each affected capability identify:

### Actor

Who or what initiates the behavior?

### Intent

What result is the actor trying to achieve?

### Entry points

Which supported routes can reach it?

### Preconditions

What must already be true?

### States

Which externally meaningful states exist?

### Transitions

Which supported actions move between states?

### Variants

Which role, permission, mode, flag, protocol, platform, provider, or environment changes behavior?

### Terminal outcomes

Consider:

- success;
- cancel;
- error;
- empty;
- timeout;
- partial completion;
- recovery;
- blocked external dependency.

### Observables

What evidence proves each transition or terminal state?

### Persistence

Which reopen, reload, restart, resume, or retry boundary must preserve state?

## Explore before constraining

When domain knowledge is incomplete, do not prematurely prescribe:

- file names;
- component ownership;
- exact architecture;
- selectors;
- commands;
- endpoints;
- internal APIs;
- test framework;
- implementation strategy.

Explore until enough evidence exists to promote an unknown into a domain contract.

Use hard constraints only where they prevent a demonstrated class of false proof or unsafe behavior.

## Knowledge classes

```text
invariant
  universal and physically enforced by the generic Skill

convention
  preferred unless repository evidence gives a reason to differ

domain contract
  stored in the consumer adapter, feature map, or product tests

incidental fact
  discovered at runtime and not promoted without repeated relevance
```

### Hard invariants

- Do not claim `VERIFIED` without production-equivalent observable evidence.
- A skipped path is not a pass.
- Do not bypass the production boundary being verified.
- Every reachable terminal has an oracle or an explicit blocked record.
- Every changed feature has at least one proof journey.
- Higher evidence layers remain unclaimed without their own receipts.

### Soft conventions

- Prefer actor-visible handles over location-dependent input.
- Prefer maintained feature documentation.
- Prefer polling stable terminal state over arbitrary sleeps.
- Prefer real supported actions over direct internal mutation.
- Prefer the smallest risk-complete journey set over a Cartesian-product explosion.

### Discoverable domain knowledge

The generic Skill does not know:

- which selector;
- which command;
- which flag;
- which endpoint;
- which component;
- which provider;
- which account;
- which environment.

Find or supply those through the domain adapter.

## Evidence hierarchy

Prefer evidence in this order:

1. observable end state from a production-equivalent path;
2. persisted or reopened observable state;
3. external integration-boundary output;
4. execution trace or telemetry tied to the same subject;
5. integration test;
6. unit test;
7. static code inspection.

Lower evidence can support higher evidence but cannot silently replace it.

A handler running, network request returning, internal state changing, mock passing, or component rendering in isolation does not prove an externally observable capability.

## Verification procedure

For every affected feature:

1. bind exact revision, environment, actor, and preconditions;
2. choose a supported entry point;
3. execute a valid transition chain;
4. observe the expected terminal state;
5. assert the behavioral contract;
6. exercise risk-distinct alternate paths;
7. verify persistence or recovery when required;
8. inspect error invariants where required;
9. record unreachable paths and blockers;
10. reconcile the coverage denominator.

Do not report complete coverage while a reachable terminal remains without a verified journey or explicit blocked record.

## Coverage reduction

The theoretical space is:

```text
actors × intents × entry points × variants × transitions × outcomes × environments
```

Do not blindly enumerate the full product.

Reduce it using:

- behavioral equivalence;
- changed feature edges;
- permission and trust boundaries;
- state-transition boundaries;
- persistence boundaries;
- platform/provider boundaries;
- known failure history;
- high-impact terminal outcomes.

The reduced set must still preserve every risk-distinct contract relevant to the change.

## Change impact

Before editing implementation, identify:

- directly affected feature;
- shared behavioral primitives;
- upstream entry points;
- downstream outcomes;
- persisted state;
- permissions and gates;
- cross-feature journeys;
- external boundaries.

After implementation, compare the code diff with the feature diff. They are different graphs.

```text
code diff
→ owned feature edges
→ required journeys
→ proof set
```

## Domain adapter contract

A consumer may provide a machine-readable adapter with:

```yaml
feature_map_root:
drivers:
selectors:
commands:
assertion_helpers:
runtime_setup:
feature_flags:
external_boundaries:
proof_artifacts:
```

Use the adapter when present. Validate its shape before driving the domain.

A domain adapter supplies concrete capabilities. It does not change the generic proof laws.

## Feature document schema

A human-readable feature document should answer only what the behavioral contract needs:

```text
Feature
Actor and intent
Sub-features
Preconditions
Entry points
Supported actions
States and transitions
Variants and gates
Observable contract
How to drive it
Assertions
Failure and recovery
Persistence
External boundaries
Related features
Known unreachable paths
```

Use the smallest schema that preserves behavior. Do not turn implementation trivia into permanent rules.

## FeatureMap IR

Machine-readable topology should declare:

- one feature identity;
- actor and intent;
- entry points and initial states;
- unique state identifiers;
- reachable transitions;
- reachable terminal outcomes;
- observable oracles;
- variants;
- persistence requirements.

Markdown owns meaning. JSON owns topology. Code owns mechanics.

## Proof-plan contract

A proof plan binds:

- exact revision and environment;
- changed feature identities;
- executable journeys;
- entry point and ordered transition IDs;
- expected terminal state;
- evidence items and boundaries;
- explicit blocked/skipped paths;
- residual uncertainty;
- final verdict.

A `VERIFIED` journey requires at least one evidence item whose kind is observable and whose boundary is `production-equivalent`, `external`, or `persisted`.

When persistence is required, a `VERIFIED` terminal also requires persisted-boundary evidence.

## Skip semantics

For every unreachable path record:

- path or terminal;
- blocker type;
- unavailable dependency;
- blocker details;
- nearest production-equivalent path exercised;
- residual uncertainty.

Use:

```text
VERIFIED
PARTIALLY_VERIFIED
BLOCKED
NOT_VERIFIED
```

Do not upgrade `PARTIALLY_VERIFIED` because implementation looks correct. Do not count a skip as a verified journey.

## Assertions

Place assertions as close as possible to observable behavior.

Prefer:

```text
observable state satisfies invariant
```

over:

```text
implementation function was called
```

Examples:

- UI state is visible and remains correct after reopen;
- API output satisfies status, schema, and idempotency contract;
- CLI returns expected exit status and durable side effect;
- workflow reaches the expected terminal state;
- agent action produces the required external state change.

Concrete assertion code belongs to the domain adapter or consumer tests.

## Meta-assertions

The portable execution layer should enforce rules such as:

```text
every changed feature has a journey
every reachable terminal has an oracle
every reachable terminal is verified or explicitly blocked
every VERIFIED claim has production-equivalent observable evidence
every required persistence boundary has persisted evidence
every skip has blocker, nearest path, and residual uncertainty
every transition chain is valid
no static-only proof is promoted
```

These generic assertions belong in shared execution code. Product-specific assertions do not.

## Updating the map

Update the feature map when:

- an actor-visible capability changes;
- an entry point changes;
- a meaningful state or transition changes;
- a gate, role, platform, protocol, or environment changes behavior;
- the observable contract changes;
- a manual path becomes executable;
- verification discovers undocumented behavior.

Do not update the feature map for implementation-only refactors that preserve the behavioral contract.

## Stop conditions

Stop with a failed or blocked result when:

- feature identity is implementation-only;
- an entry point cannot reach the declared state;
- a transition chain is invalid;
- a reachable terminal lacks an oracle;
- a changed feature lacks a journey;
- `VERIFIED` has only static, unit, mock, or internal evidence;
- required persistence lacks persisted evidence;
- an unreachable path lacks a blocker or residual uncertainty;
- the current environment cannot exercise the claimed production boundary;
- documentation and runtime conflict without being reconciled.

## Completion

A task is complete when:

- the behavioral contract is identified;
- implementation satisfies it;
- relevant reachable variants are exercised;
- observable evidence is captured;
- unreachable paths are explicitly admitted;
- coverage is reconciled;
- the feature map matches runtime reality;
- the evidence ceiling is stated without promotion.

Code completion alone is not feature completion.
