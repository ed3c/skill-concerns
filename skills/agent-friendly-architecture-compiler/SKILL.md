---
name: agent-friendly-architecture-compiler
description: >
  Compile evidence-backed architecture knowledge into a self-contained Agent-Friendly
  Architecture contract that a zero-context coding LLM can use to infer the Best Path.
  Supports two Skill modes: Domain-rich and Procedure-rich/Domain-decoupled. BUILD is
  the only writer role; SHADOW is a read-only reviewer.
---

# Agent-Friendly Architecture Compiler

## Goal

Produce one direct Agent-facing architecture contract that explains enough system logic for a coding LLM to choose the correct local implementation path without requiring hidden knowledge of the source framework, source repository, evidence ontology, or compiler internals.

The output is not a summary of a source system. It is evidence-backed architecture knowledge compiled into a decision contract.

## Naming law

Do not overload `L0/L1/L2`.

In this Skill:

```text
L0/L1/L2 = Skill concern stack
P0/P1/P2 = rendered-product compilation stack
S0/S1/S2 = SHADOW review severity
```

These are separate axes and must not be substituted for one another.

## Skill concern stack — L0 / L1 / L2

### L0 — PROCEDURAL SKILL

Portable, domain-independent method.

L0 owns:
- mode selection;
- evidence-to-semantics procedure;
- exploration policy;
- generalization and compression laws;
- self-containedness tests;
- Best Path preservation tests;
- proof semantics and stop conditions.

L0 must not absorb repository-specific commands, paths, selectors, ownership facts, provider identities, runtime state, or product-specific assertions.

### L1 — DOMAIN KNOWLEDGE

Consumer-repository/product knowledge needed to instantiate L0 correctly.

L1 may contain:
- capabilities, states, entry points, and extension surfaces;
- domain vocabulary and architecture primitives;
- canonical owners/writers;
- package/import boundaries;
- selectors, commands, feature flags, fixtures, and environment constraints;
- known exceptions and failure modes;
- source evidence needed to distinguish actual architecture from analogy.

`DOMAIN_RICH` may preserve selected L1 concepts in the final contract only when they are load-bearing and defined in-place.

`PROCEDURE_RICH_DOMAIN_DECOUPLED` consumes L1 but removes source-specific black boxes from the reusable product.

### L2 — EXECUTION + ASSERTIONS

Concrete actions and proof mechanisms.

L2 may:
- inspect repository/runtime state;
- act through supported interfaces;
- poll and synchronize;
- run static analysis, compiler, lint, CI, tests, or domain drivers;
- observe relevant outcomes;
- assert invariants;
- execute planted negative controls;
- persist and read back evidence.

L2 proves or falsifies a concrete domain realization. It cannot silently redefine L0 portable policy or promote one repository mechanism into a universal architecture rule.

```text
L0 PROCEDURAL SKILL
        ↓ applies to
L1 DOMAIN KNOWLEDGE
        ↓ grounded/proven by
L2 EXECUTION + ASSERTIONS
```

## Two Skill modes

Select exactly one mode before compilation.

### Mode A — DOMAIN_RICH

Use when domain nouns are themselves part of the executable architecture and removing them would destroy the Best Path.

A Domain-rich output may preserve repository/product-specific nouns, paths, commands, state owners, extension surfaces, or runtime concepts only when it defines them in-place and they materially change the consumer's correct decision.

Domain-specific does not mean black-box.

### Mode B — PROCEDURE_RICH_DOMAIN_DECOUPLED

Use when architecture knowledge should transfer across repositories.

Remove source-system nouns and preserve only architectural pressure needed for correct decisions. Render every required concept in ordinary architecture language.

A zero-context coding LLM must be able to use the result without prior knowledge of Dune, Noodle, noodles, P/L/R/N, FeatureMap, Spatial Loop, or another source framework.

Use this mode by default for reusable Agent-Friendly Architecture guidance.

## BUILD and SHADOW roles

`BUILD` and `SHADOW` are orthogonal roles available in either Skill mode.

```text
DOMAIN_RICH
  ├── BUILD
  └── SHADOW

PROCEDURE_RICH_DOMAIN_DECOUPLED
  ├── BUILD
  └── SHADOW
```

### BUILD

BUILD is the sole candidate writer.

It consumes L0 procedure + L1 domain knowledge + available L2 evidence, then produces P0 → P1 → P2.

### SHADOW

SHADOW reads the same evidence and BUILD output, produces findings only, and never creates a competing implementation.

It looks for:
- black-box vocabulary;
- semantic degradation;
- unsupported generalization;
- lost negative knowledge;
- authority laundering;
- wrong Best Path inference.

Use these severity names so they cannot be confused with Skill layers:

### S0 OBSERVE

Record a non-load-bearing concern. Do not interrupt BUILD.

### S1 WARN

Expose a material ambiguity, evidence limitation, or narrower safe interpretation. BUILD may continue while the limitation is explicit.

### S2 REVIEW

Require reconciliation before publication when a consumer can reasonably infer a wrong Best Path.

Examples:
- unexplained domain/framework vocabulary is required to understand the contract;
- domain-decoupled mode leaks a source implementation as a universal rule;
- domain-rich mode uses a domain primitive without defining its architectural role;
- a load-bearing invariant disappears during compression;
- a negative claim or exception is omitted and a stronger interpretation becomes plausible;
- guidance is rendered as mechanical enforcement;
- a new abstraction layer increases normal-path decisions without closing a demonstrated failure;
- the output describes the source control system instead of reusable architecture knowledge.

## Rendered-product compilation stack — P0 / P1 / P2

These stages describe the product generated from the Skill stack. They are not Skill concern layers.

### P0 — Semantic Kernel

Extract the load-bearing architecture pressure that must survive removal or compression of source-specific representation.

Examples:
- narrow-context Agents imitate local precedent;
- conventional paths should require fewer decisions than shortcuts;
- deterministic invariants belong at the strongest practical enforcement layer;
- durable truth should have one obvious writer;
- extension should prefer isolated surfaces over shared-root branching;
- repeated deterministic failures should migrate from review prose into mechanisms.

### P1 — Self-contained Contract

Render P0 into direct Agent-facing architecture language. Every concept required to infer the Best Path must be defined in-place.

For domain-decoupled mode, understanding must not depend on source-system knowledge.

For domain-rich mode, domain primitives may remain only when the contract itself defines their responsibility, allowed operations, constraints, and Best Path consequence.

### P2 — Best Path Procedure

Turn P1 into a concrete repository-change decision procedure.

The consumer should be able to:
1. identify the required outcome;
2. locate the nearest correct precedent;
3. find the canonical owner/writer of affected durable state;
4. identify supported dependency and extension boundaries;
5. detect conflicts with invariants;
6. prefer isolated extension over shared-root branching;
7. choose the smallest architecture-preserving change;
8. execute the strongest available verification;
9. exercise relevant negative/failure paths;
10. move repeated deterministic failures toward stronger enforcement.

P2 must not require compiler metadata.

## BUILD procedure

1. Select `DOMAIN_RICH` or `PROCEDURE_RICH_DOMAIN_DECOUPLED`.
2. Apply the portable L0 procedure.
3. Bind the exact L1 domain knowledge relevant to the task.
4. Identify available L2 execution/assertion evidence and its limits.
5. Separate source statements, repository observations, executable evidence, and inference.
6. Identify the contributor-context model: what a local Agent is likely to see and imitate.
7. Extract P0 candidate invariants from architectural pressures, not source vocabulary alone.
8. Apply the mode-specific vocabulary test:
   - Domain-rich: retain a domain noun only when load-bearing, defined in-place, and required for the Best Path.
   - Domain-decoupled: remove a source noun unless its meaning can be expressed as a portable architecture primitive.
9. Preserve material divergence, exceptions, failure modes, and negative knowledge whenever deletion could permit a stronger or wrong Best Path inference.
10. Render P1 before P2. Explain why before prescribing procedure.
11. Keep schemas, manifests, evidence IDs, graphs, confidence classes, and comparison machinery outside the normal rendered reading path unless a Domain-rich consumer genuinely needs one as an executable primitive.
12. Prefer the shortest wording that preserves every load-bearing invariant.
13. Run SHADOW S0/S1/S2 review and deterministic checks before publication.

## Self-containedness test

For `PROCEDURE_RICH_DOMAIN_DECOUPLED`, ask:

> Given only P1/P2 and an unfamiliar repository, can a fresh coding LLM explain how to choose the architecture-preserving Best Path and why an unsafe shortcut is wrong?

For `DOMAIN_RICH`, ask:

> Given only P1/P2 and repository files explicitly routed by the contract, can a fresh coding LLM understand every domain primitive required for the Best Path without undocumented organizational knowledge?

Fail when either answer depends on hidden context.

## Best Path preservation test

For every material insight, check both directions:

```text
L1 domain evidence + L2 observations
-> P0 semantic kernel
-> P1 architecture rule
-> P2 decision consequence
```

and:

```text
P1/P2 rendered rule
-> plausible local Agent inference
-> does that inference remain inside the evidence-backed architecture pressure?
```

If the second chain can produce a stronger or wrong instruction, narrow or rewrite the product.

## Anti-overengineering test

Before introducing any compiler layer or consumer concept, ask:

1. What demonstrated failure does it prevent?
2. Could an existing boundary prevent the same failure?
3. Does it reduce or increase decisions on the normal path?
4. Is it another source of truth?
5. Can it remain a private compiler/validation concern instead of a consumer concept?

Default to keeping schemas, evidence manifests, graph projections, and validators off the hot path.

## Completion

A candidate is complete at this Skill's procedure level when:

- the Skill mode is explicit;
- L0 procedure remained domain-independent;
- required L1 knowledge is explicit rather than hidden;
- L2 evidence/assertion limits are preserved;
- P0 retains the load-bearing semantic kernel;
- P1 is self-contained under the selected mode;
- P2 yields a direct Best Path decision procedure;
- SHADOW has no unresolved S2 findings;
- deterministic checks reject planted black-box and semantic-loss cases;
- wording does not imply an evidence layer that was not reached.
