---
name: agent-friendly-architecture-compiler
description: >
  Compile evidence-backed architecture knowledge into a self-contained Agent-Friendly
  Architecture contract that a coding LLM can use to infer the Best Path. Supports
  DOMAIN_RICH and PROCEDURE_RICH_DOMAIN_DECOUPLED modes. BUILD is the sole writer;
  SHADOW is a read-only reviewer.
---

# Agent-Friendly Architecture Compiler

## Goal

Compile architecture knowledge into a direct Agent-facing contract. The consumer must not need hidden knowledge of the source framework, repository, evidence ontology, or compiler internals to choose the correct implementation path.

The output is not a summary of the source system. It is evidence-backed architecture knowledge transformed into a decision contract.

## Naming law

Keep these namespaces separate:

```text
Skill concern stack:   L0 PROCEDURAL SKILL → L1 DOMAIN KNOWLEDGE → L2 EXECUTION + ASSERTIONS
Compilation stages:    C0 Semantic Kernel → C1 Self-contained Contract → C2 Best Path Procedure
Execution roles:       BUILD | SHADOW
Shadow severity:       S0 OBSERVE | S1 WARN | S2 REVIEW
Skill modes:           DOMAIN_RICH | PROCEDURE_RICH_DOMAIN_DECOUPLED
```

`C` means **Compilation**. Never use `P0/P1/P2` for the compilation stages: `P` can be misread as priority and conflicts with evidence vocabularies such as `P/L/R/N`.

## Two Skill modes

### DOMAIN_RICH

Use when concrete repository/product primitives are themselves load-bearing architecture and removing them would destroy the Best Path.

A Domain-rich result may retain nouns, paths, commands, state owners, extension surfaces, selectors, flags, or runtime concepts only when:

- they materially change the Best Path;
- they are defined in-place;
- their ownership/constraints are explicit;
- no undocumented organizational knowledge is required.

Domain-specific must not mean black-box.

### PROCEDURE_RICH_DOMAIN_DECOUPLED

Use when the architecture knowledge should transfer across repositories. Remove source-system vocabulary and preserve the reusable architecture pressure required for correct decisions.

A zero-context coding LLM must be able to consume C1/C2 without prior knowledge of Dune, Noodle, noodles, FeatureMap, Spatial Loop, evidence enums, or compiler machinery.

This is the default mode for reusable Agent-Friendly Architecture guidance.

## Skill concern stack

### L0 — PROCEDURAL SKILL

Portable/domain-independent procedure. Owns:

- mode selection;
- exploration policy;
- extraction procedure;
- semantic-preservation rules;
- negative-knowledge preservation;
- Best Path reasoning policy;
- stop conditions and proof semantics.

### L1 — DOMAIN KNOWLEDGE

Concrete repository/product knowledge. May include:

- capabilities and states;
- entry points and extension surfaces;
- owners/writers;
- package/import boundaries;
- selectors and feature flags;
- environment constraints;
- domain-specific exceptions/failure modes;
- repository evidence needed to distinguish architecture from analogy.

In DOMAIN_RICH mode, selected L1 primitives may survive into C1 only if self-defined and load-bearing. In domain-decoupled mode, L1 is compilation input, not portable output.

### L2 — EXECUTION + ASSERTIONS

Concrete mechanisms that act, poll, observe, assert, persist, and read back evidence:

- repository analyzers;
- static/compiler/lint/CI checks;
- tests and drivers;
- runtime probes;
- planted negative controls;
- evidence persistence/readback.

L2 proves or falsifies domain realizations. It must not silently become a universal C0 rule.

## Compilation stages

### C0 — Semantic Kernel

Extract the source-independent architecture pressure that must survive compression.

Ask: **What survives domain removal?**

Typical candidates include:

- narrow-context Agents imitate local precedent;
- conventional paths should require fewer decisions than shortcuts;
- invalid states should fail at the strongest practical deterministic layer;
- durable truth should have one obvious writer;
- extensions should prefer isolated surfaces over shared-root branching;
- repeated deterministic review failures should migrate from prose into mechanisms.

A source-specific implementation is not automatically a C0 invariant.

### C1 — Self-contained Contract

Render C0 into ordinary architecture language. Define every concept required for correct reasoning in-place.

Ask: **What must the Agent understand?**

A consumer should be able to determine from C1 alone:

- the contributor-context assumptions;
- preferred repository shape;
- what counts as a shortcut;
- where deterministic enforcement belongs;
- how state ownership works;
- how exceptions are bounded;
- why Greenfield, rewrite, and repeated-review failures create architecture risk.

For domain-decoupled mode, hidden source vocabulary is a failure. For Domain-rich mode, a retained primitive is acceptable only when C1 itself explains its architectural responsibility and constraints.

### C2 — Best Path Procedure

Turn C1 into a concrete repository-change decision procedure.

Ask: **What should the Agent do?**

The consumer should be able to:

1. identify the required outcome;
2. locate the nearest correct precedent;
3. identify the canonical owner/writer of affected durable state;
4. identify supported dependency and extension boundaries;
5. detect conflicts with invariants;
6. prefer isolated extension over shared-root branching;
7. choose the smallest architecture-preserving change;
8. execute the strongest available verification;
9. exercise relevant negative/failure paths;
10. move recurring deterministic failures toward stronger enforcement.

C2 must not require compiler metadata.

## Execution roles

### BUILD

BUILD is the only writer. It consumes L0 procedure + L1 domain knowledge + available L2 evidence and produces C0 → C1 → C2.

BUILD procedure:

1. Select the Skill mode explicitly.
2. Freeze the exact source/repository evidence available.
3. Separate source statements, repository observations, executable evidence, and inference.
4. Identify the contributor-context model: what a local Agent can actually see and imitate.
5. Extract candidate architecture pressures without assuming source nouns are universal.
6. Apply the vocabulary test:
   - DOMAIN_RICH: retain only load-bearing primitives defined in-place.
   - PROCEDURE_RICH_DOMAIN_DECOUPLED: remove source nouns unless their meaning can be expressed as a portable primitive.
7. Preserve material divergence, exceptions, failure modes, and negative knowledge when deleting them could produce a stronger or wrong Best Path inference.
8. Produce C0 before C1, and C1 before C2.
9. Keep schemas, claim IDs, evidence manifests, graphs, and comparison machinery outside the rendered hot path unless genuinely required by a Domain-rich executable primitive.
10. Prefer the shortest wording that preserves every load-bearing distinction.
11. Run SHADOW and deterministic checks before publication.

### SHADOW

SHADOW is read-only. It reviews the same evidence plus BUILD output and never creates a competing implementation.

It looks for:

- black-box vocabulary;
- semantic degradation;
- unsupported generalization;
- lost negative knowledge;
- authority laundering;
- wrong Best Path inference;
- additional conceptual layers that increase normal-path decisions without closing a demonstrated failure.

#### S0 — OBSERVE

Record non-load-bearing concerns. No publication interruption.

#### S1 — WARN

Use for material ambiguity or evidence/semantic limitation whose safe interpretation can be stated explicitly.

#### S2 — REVIEW

Use when the declared mode's consumer can reasonably infer a wrong Best Path, including:

- unexplained domain/framework vocabulary;
- domain-specific implementation presented as a universal C0 rule;
- load-bearing invariant lost during compression;
- omitted exception/negative knowledge allowing a stronger interpretation;
- guidance rendered as mechanical enforcement;
- output describing the source control system instead of the architecture knowledge the consumer needs.

S2 must be reconciled before publication. It is not a style veto.

## Self-containedness tests

For PROCEDURE_RICH_DOMAIN_DECOUPLED ask:

> Given only C1/C2 and an unfamiliar repository, can a fresh coding LLM explain how to choose the architecture-preserving Best Path and why an unsafe shortcut is wrong?

For DOMAIN_RICH ask:

> Given only C1/C2 and the repository files explicitly routed by the contract, can a fresh coding LLM understand every Best-Path-critical domain primitive without undocumented organizational knowledge?

Fail when the answer depends on hidden context.

## Best Path preservation test

Check both directions for every material insight:

```text
source/repository evidence
→ C0 architecture pressure
→ C1 contract rule
→ C2 decision consequence
```

and:

```text
C1 rule
→ plausible local Agent inference
→ does the inference remain inside the evidence-backed architecture pressure?
```

If a plausible inference becomes stronger or points to the wrong Best Path, narrow or rewrite it.

## Anti-overengineering test

Before introducing a compiler layer or consumer concept, ask:

1. What demonstrated failure does it prevent?
2. Could the nearest existing boundary prevent the same failure?
3. Does it reduce or increase decisions on the normal path?
4. Does it create another source of truth?
5. Can it remain private compiler/validation machinery rather than a consumer concept?

Default to keeping schema/evidence/graph machinery off the Agent hot path.

## Completion

Procedure-level completion requires:

- Skill mode explicit;
- L0/L1/L2 concern ownership preserved;
- C0 retains the load-bearing semantic kernel;
- C1 is self-contained for the selected mode;
- C2 yields a direct Best Path procedure;
- no unresolved S2 findings;
- deterministic checks reject planted black-box/semantic-loss cases;
- wording does not imply an evidence layer not physically reached.
