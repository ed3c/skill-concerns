# Rendered Product Contract

The final product is a self-contained Markdown architecture contract for a zero-context coding LLM.

This reference uses `P0/P1/P2` for rendered-product compilation stages. `L0/L1/L2` are reserved for the Skill concern stack:

```text
L0 PROCEDURAL SKILL
L1 DOMAIN KNOWLEDGE
L2 EXECUTION + ASSERTIONS

P0 Semantic Kernel
P1 Self-contained Contract
P2 Best Path Procedure
```

The rendered product is derived from the Skill stack; it is not the Skill stack itself.

## P0 — Semantic Kernel

Preserve the source-independent architectural pressure that changes how a consumer should reason.

Examples:
- local Agents imitate nearby precedent;
- the conventional path should require fewer decisions than a shortcut;
- deterministic invariants belong at the strongest practical enforcement layer;
- durable truth should have one obvious writer;
- isolated extension surfaces are safer than shared-root branching;
- repeated deterministic review failures should migrate into mechanisms.

## P1 — Self-contained Contract

Render P0 into ordinary architecture language. Define every concept required for Best Path inference in-place.

For a reusable domain-decoupled product, P1 must not require prior knowledge of a source project, private role names, internal control planes, evidence enums, compiler schemas, graph systems, or other black boxes.

For a Domain-rich product, a domain primitive may remain only when the same rendered contract explains what it is, what it owns, what operations are allowed, what constraints apply, and how it changes the Best Path.

## P2 — Best Path Procedure

Convert P1 into an actionable repository-change decision rule. The consumer must be able to choose the smallest architecture-preserving, mechanically verifiable path without compiler metadata.

## Required semantic sections

The rendered contract should directly explain:

1. Context Model — what local information an Agent usually has and how that shapes behavior.
2. Core Architecture Rules — conventional path, mechanical rejection, single writer, isolated extension surfaces, explicit exceptions.
3. Enforcement Hierarchy — strongest deterministic layer first; prose last.
4. Shortest Path Should Be the Best Path — local imitation must be made safe by repository defaults and hard constraints.
5. Greenfield Systems — establish an executable Golden Path before bad precedent compounds.
6. Human Slop and Agent Slop — repeated deterministic review knowledge migrates into mechanisms.
7. Rewrite Safety — preserve observable behavior/invariants through an executable migration contract.
8. Adding New Architecture — reject layers that increase normal-path concepts without closing a demonstrated failure.
9. Implementation Procedure — concrete repository-change decision sequence.
10. Best Path Decision Rule — maximize local obviousness, precedent, isolation, ownership, mechanical enforcement, verifiability; minimize new concepts, shared-root edits, manual registration, duplicate state, implicit exceptions, prose-only invariants, and human-only verification.

## Evidence boundary

Evidence comes from L1 domain knowledge and L2 execution/assertions and protects compilation, but evidence syntax should not dominate consumption. Claim IDs, receipts, schemas, manifests, and audit syntax remain sidecar concerns unless a Domain-rich consumer genuinely needs one as an executable primitive.

The rendered product may never state a stronger rule than the underlying evidence permits.

## Compression law

Shortening is allowed only when it does not remove a load-bearing invariant, exception, failure condition, or distinction whose absence changes plausible Best Path inference.

A shorter contract that creates a stronger unsupported instruction is worse than a longer self-contained one.
