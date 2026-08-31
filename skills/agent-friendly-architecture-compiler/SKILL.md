---
name: agent-friendly-architecture-compiler
description: >
  Compile source-specific architecture evidence into a self-contained Agent-Friendly
  Architecture contract that a zero-context coding LLM can use to infer the Best Path
  in an unfamiliar repository. Use BUILD mode to author the contract and SHADOW mode
  to detect black-box vocabulary, semantic drift, lost invariants, unsupported
  generalization, authority laundering, and wrong Best Path inference.
---

# Agent-Friendly Architecture Compiler

## Goal

Produce one direct Agent-facing architecture contract that explains enough of the system logic for a coding LLM to choose the correct local implementation path without knowing the source framework, source repository, evidence ontology, or compiler internals.

The output is not a summary of the source system. It is the source system's evidence-backed architectural knowledge compiled into a self-contained decision contract.

## Mode selection

Use exactly one writing mode and one optional review mode:

- `BUILD`: owns candidate generation and edits.
- `SHADOW`: observes the same inputs and candidate, produces findings only, and never edits the candidate.

Run SHADOW whenever the source contains domain-specific machinery, the output is intended for reuse outside that domain, or compression could remove exception/failure knowledge.

## Product layers

### Product L0 — Semantic Kernel

Extract only the architecture pressure that survives removal of source-specific nouns.

Examples:

- narrow-context Agents imitate local precedent;
- the conventional path should require fewer decisions than a shortcut;
- invalid states should fail at the strongest deterministic layer available;
- durable truth should have one obvious writer;
- extension should prefer isolated surfaces over shared-root branching;
- repeated deterministic failures should migrate from review prose into mechanisms.

Do not copy product nouns into L0 unless the noun itself is a universal architectural primitive.

### Product L1 — Self-contained Contract

Render the kernel into plain architecture language. Define every concept needed by the consumer in-place.

A zero-context coding LLM must be able to answer from L1 alone:

- what local Agent behavior the architecture assumes;
- what repository shape it should prefer;
- what counts as a shortcut;
- where deterministic enforcement belongs;
- how ownership and exceptions work;
- why Greenfield, rewrite, and repeated review failures are dangerous.

If answering requires knowledge of Dune, Noodle, noodles, P/L/R/N, FeatureMap, or any source-specific framework, L1 fails.

### Product L2 — Best Path Procedure

Turn the contract into a concrete implementation decision rule.

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

1. Freeze the exact source and target-repository evidence available to the task.
2. Separate source statements, repository observations, executable evidence, and inference.
3. Identify the contributor-context model: what a local Agent is likely to see and imitate.
4. Extract candidate invariants from repeated architectural pressures, not from source vocabulary alone.
5. For every candidate invariant, ask whether removing the source-specific noun preserves the meaning. If not, either define the noun in-place as a target primitive or keep the statement domain-specific outside the portable contract.
6. Preserve material divergence, exceptions, failure modes, and negative knowledge when deleting them could allow a stronger or wrong Best Path inference.
7. Render Product L1 before adding Product L2. The contract should explain why before prescribing procedure.
8. Keep evidence IDs, schemas, manifests, graphs, confidence classes, and source-comparison machinery outside the normal rendered reading path.
9. Prefer the shortest wording that still preserves every load-bearing invariant required for correct Best Path reasoning.
10. Run SHADOW review and deterministic structural checks before publication.

## SHADOW procedure

SHADOW reads source evidence plus BUILD output and emits findings using only these intervention levels:

### L0 OBSERVE

Use when there may be a non-load-bearing issue:

- wording could be shorter;
- an example is slightly domain-flavored but defined and harmless;
- a source detail may be redundant.

Record only. Do not interrupt BUILD.

### L1 WARN

Use when the output may mislead but the candidate can continue while the limitation is explicit:

- a claim has a lower evidence ceiling than its wording suggests;
- a source-specific noun is defined but unnecessarily prominent;
- a divergence or exception is compressed enough to create ambiguity;
- an architecture recommendation is supported only as a convention, not a hard invariant.

State the likely misread and the narrower safe interpretation.

### L2 REVIEW

Use only when a zero-context Agent can reasonably infer a wrong Best Path:

- unexplained source/framework vocabulary is required to understand the contract;
- a source-specific implementation is presented as a universal architecture rule without semantic support;
- a load-bearing invariant disappears during compression;
- a negative claim/exception is omitted and the stronger interpretation becomes plausible;
- guidance is rendered as mechanical enforcement;
- a new abstraction layer increases normal-path decisions without closing a demonstrated failure;
- the output describes the source control system instead of the reusable architecture knowledge.

L2 requires reconciliation before the next publication checkpoint. It is not a style veto.

## Self-containedness test

Before publication, mentally remove all external names and ask a fresh coding LLM:

> Given only this rendered contract and an unfamiliar repository, can you explain how to choose the architecture-preserving Best Path and what evidence would make you distrust a shortcut?

Fail if the answer depends on undocumented external vocabulary or hidden source knowledge.

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
-> does that inference stay within the evidence-backed architecture pressure?
```

If the second chain can produce a stronger or wrong instruction, narrow or rewrite the rendered rule.

## Anti-overengineering test

Before introducing any compiler layer or output concept, ask:

1. What demonstrated failure does it prevent?
2. Could an existing boundary prevent the same failure?
3. Does it reduce or increase concepts on the consumer's normal path?
4. Is it another source of truth?
5. Can it remain a private compiler/validation concern instead of a consumer concept?

Default to keeping schemas, evidence manifests, graph projections, and validators off the hot path.

## Completion

A candidate is complete at this Skill's procedure level when:

- Product L0 preserves the source-independent semantic kernel;
- Product L1 is self-contained and contains no required unexplained source-system knowledge;
- Product L2 yields a direct Best Path decision procedure;
- SHADOW has no unresolved L2 findings;
- deterministic checks confirm required sections and planted black-box/semantic-loss failures are rejected;
- higher evidence layers are not implied by wording.
