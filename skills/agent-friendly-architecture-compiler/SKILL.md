---
name: agent-friendly-architecture-compiler
description: >
  Compile evidence-backed architecture knowledge into a self-contained Agent-Friendly
  Architecture contract that a zero-context coding LLM can use to infer the Best Path.
  Supports two target modes: Domain-rich and Procedure-rich/Domain-decoupled. BUILD is
  the only writer role; SHADOW is a read-only reviewer with L0/L1/L2 intervention levels.
---

# Agent-Friendly Architecture Compiler

## Goal

Produce one direct Agent-facing architecture contract that explains enough system logic for a coding LLM to choose the correct local implementation path without requiring hidden knowledge of the source framework, source repository, evidence ontology, or compiler internals.

The output is not a summary of a source system. It is evidence-backed architecture knowledge compiled into a decision contract.

## Two Skill modes

Select exactly one product mode before compilation.

### Mode A — Domain-rich Skill

Use when domain nouns are themselves part of the executable architecture and removing them would destroy the Best Path.

A Domain-rich output may preserve repository/product-specific nouns, paths, commands, state owners, extension surfaces, or runtime concepts only when it defines them in-place and binds them to the domain's actual architecture.

The consumer must not need hidden background knowledge. Domain-specific does not mean black-box.

Use Domain-rich mode when:

- the Skill will operate inside one known product/repository family;
- concrete domain primitives are required to choose the correct path;
- the domain realization is stable enough to be a maintained contract;
- removing the domain vocabulary would make the instruction less correct, not merely less reusable.

### Mode B — Procedure-rich / Domain-decoupled Skill

Use when the objective is to extract architecture knowledge that should transfer across repositories.

Remove source-system nouns and preserve only the architectural pressure needed for correct decisions. Render every required concept in ordinary architecture language.

A zero-context coding LLM must be able to use the output without knowing Dune, Noodle, noodles, P/L/R/N, FeatureMap, Spatial Loop, or another source framework.

Use this mode by default for reusable Agent-Friendly Architecture guidance.

## Orthogonal execution roles

`BUILD` and `SHADOW` are not Skill modes. They are roles that can be applied to either mode.

```text
Domain-rich
  ├── BUILD   # only writer
  └── SHADOW  # read-only reviewer

Procedure-rich / Domain-decoupled
  ├── BUILD   # only writer
  └── SHADOW  # read-only reviewer
```

### BUILD

BUILD is the sole candidate writer. It owns evidence → semantic kernel → self-contained contract → Best Path.

### SHADOW

SHADOW reads the same evidence and BUILD output, produces findings only, and never creates a competing implementation. It looks specifically for:

- black-box vocabulary;
- semantic degradation;
- unsupported generalization;
- lost negative knowledge;
- authority laundering;
- wrong Best Path inference.

## Product layers

The following layers describe the produced knowledge, not the BUILD/SHADOW roles.

### L0 — Semantic Kernel

Extract the architecture pressure that must survive compression.

Examples:

- narrow-context Agents imitate local precedent;
- conventional paths should require fewer decisions than shortcuts;
- invalid states should fail at the strongest practical deterministic layer;
- durable truth should have one obvious writer;
- extension should prefer isolated surfaces over shared-root branching;
- repeated deterministic failures should migrate from review prose into mechanisms.

In Domain-rich mode, L0 may retain a domain primitive only when that primitive is itself load-bearing and defined by the output. In Domain-decoupled mode, source-specific nouns must not survive merely because they were prominent in the source.

### L1 — Self-contained Contract

Render L0 into direct architecture language. Every concept needed to infer the Best Path must be defined in-place.

The consumer must be able to answer:

- what local Agent behavior the architecture assumes;
- what repository shape it should prefer;
- what counts as a shortcut;
- where deterministic enforcement belongs;
- how ownership and exceptions work;
- why Greenfield, rewrite, and repeated review failures are dangerous.

A Domain-rich L1 may use domain vocabulary only when the document itself makes that vocabulary non-black-box. A Domain-decoupled L1 fails if understanding depends on source-system knowledge.

### L2 — Best Path Procedure

Turn the contract into a concrete decision procedure.

For a repository change, the consumer should be able to:

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

L2 must not require compiler metadata.

## BUILD procedure

1. Select Domain-rich or Procedure-rich/Domain-decoupled mode explicitly.
2. Freeze the exact source and target-repository evidence available to the task.
3. Separate source statements, repository observations, executable evidence, and inference.
4. Identify the contributor-context model: what a local Agent is likely to see and imitate.
5. Extract candidate invariants from repeated architectural pressures, not from source vocabulary alone.
6. Apply the mode-specific vocabulary test:
   - Domain-rich: retain a domain noun only when it is load-bearing, defined in-place, and needed for the Best Path.
   - Domain-decoupled: remove a source noun unless its meaning can be rewritten as a portable architectural primitive.
7. Preserve material divergence, exceptions, failure modes, and negative knowledge whenever deleting them could permit a stronger or wrong Best Path inference.
8. Render L1 before L2. Explain why before prescribing procedure.
9. Keep evidence IDs, schemas, manifests, graphs, confidence classes, and source-comparison machinery outside the normal rendered reading path unless a Domain-rich consumer explicitly needs one as an executable primitive.
10. Prefer the shortest wording that preserves every load-bearing invariant.
11. Run SHADOW review and deterministic structural checks before publication.

## SHADOW procedure

SHADOW uses the same intervention levels in either Skill mode.

### L0 OBSERVE

Use for non-load-bearing issues such as wording that could be shorter or an example that is harmless but slightly domain-flavored.

Record only. Do not interrupt BUILD.

### L1 WARN

Use when the output may mislead but can continue while the limitation is explicit, for example an evidence ceiling narrower than the wording or a compressed exception that creates ambiguity.

State the likely misread and the narrower safe interpretation.

### L2 REVIEW

Use when a zero-context consumer of the declared Skill mode can reasonably infer a wrong Best Path:

- unexplained domain/framework vocabulary is required to understand the contract;
- Domain-decoupled mode leaks source-specific implementation as a universal rule;
- Domain-rich mode uses domain nouns without defining their role in the architecture;
- a load-bearing invariant disappears during compression;
- a negative claim or exception is omitted and a stronger interpretation becomes plausible;
- guidance is rendered as mechanical enforcement;
- a new abstraction layer increases normal-path decisions without closing a demonstrated failure;
- the output describes the source control system instead of the architecture knowledge the consumer actually needs.

L2 requires reconciliation before publication. It is not a style veto.

## Self-containedness test

For Domain-decoupled mode, remove all external names and ask:

> Given only this rendered contract and an unfamiliar repository, can a fresh coding LLM explain how to choose the architecture-preserving Best Path and why an unsafe shortcut is wrong?

For Domain-rich mode, ask:

> Given only this rendered contract and the repository files it explicitly routes to, can a fresh coding LLM understand every domain primitive required for the Best Path without undocumented organizational knowledge?

Fail when either answer depends on hidden context.

## Best Path preservation test

For every material source insight, check both directions:

```text
source evidence
-> rendered architecture rule
-> consumer decision consequence
```

and:

```text
rendered architecture rule
-> plausible local Agent inference
-> does that inference stay inside the evidence-backed architecture pressure?
```

If the second chain can produce a stronger or wrong instruction, narrow or rewrite the contract.

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

- the target mode is explicit;
- L0 preserves the load-bearing semantic kernel;
- L1 is self-contained under that mode's context contract;
- L2 yields a direct Best Path decision procedure;
- SHADOW has no unresolved L2 findings;
- deterministic checks reject planted black-box and semantic-loss cases;
- wording does not imply an evidence layer that was not reached.
