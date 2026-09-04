# Rendered Product Contract

The final product is a self-contained Markdown architecture contract for a coding LLM.

## Namespace separation

```text
Skill concern stack
L0 PROCEDURAL SKILL
L1 DOMAIN KNOWLEDGE
L2 EXECUTION + ASSERTIONS

Compilation stages
C0 Semantic Kernel
C1 Self-contained Contract
C2 Best Path Procedure

Shadow severity
S0 OBSERVE
S1 WARN
S2 REVIEW
```

`C` means **Compilation**. Do not use `P0/P1/P2`: `P` is commonly read as priority and may collide with evidence vocabularies such as `P/L/R/N`.

The rendered product is derived from the Skill stack; it is not the Skill stack itself.

## C0 — Semantic Kernel

Preserve the source-independent architecture pressure that changes how a consumer should reason.

Ask: **What survives domain removal?**

Examples:
- local Agents imitate nearby precedent;
- the conventional path should require fewer decisions than a shortcut;
- deterministic invariants belong at the strongest practical enforcement layer;
- durable truth should have one obvious writer;
- isolated extension surfaces are safer than shared-root branching;
- repeated deterministic review failures should migrate into mechanisms.

## C1 — Self-contained Contract

Render C0 into ordinary architecture language. Define every concept required for Best Path inference in-place.

Ask: **What must the Agent understand?**

For a reusable domain-decoupled product, C1 must not require prior knowledge of a source project, private role names, control planes, evidence enums, compiler schemas, graph systems, or other black boxes.

For a Domain-rich product, a domain primitive may remain only when the same contract explains what it is, what it owns, what operations are allowed, what constraints apply, and how it changes the Best Path.

## C2 — Best Path Procedure

Convert C1 into an actionable repository-change decision rule.

Ask: **What should the Agent do?**

The consumer must be able to choose the smallest architecture-preserving, mechanically verifiable path without compiler metadata.

## Required semantic sections

The rendered contract should directly explain:

1. Context Model — what local information an Agent usually has and how that shapes behavior.
2. Core Architecture Rules — conventional path, mechanical rejection, single writer, isolated extension surfaces, explicit exceptions.
3. Enforcement Hierarchy — strongest deterministic layer first; prose last.
4. Shortest Path Should Be the Best Path — local imitation made safe by repository defaults and hard constraints.
5. Greenfield Systems — establish an executable Golden Path before bad precedent compounds.
6. Human Slop and Agent Slop — repeated deterministic review knowledge migrates into mechanisms.
7. Rewrite Safety — preserve observable behavior/invariants through an executable migration contract.
8. Adding New Architecture — reject layers that increase normal-path concepts without closing a demonstrated failure.
9. Implementation Procedure — concrete repository-change decision sequence.
10. Best Path Decision Rule — maximize local obviousness, precedent, isolation, ownership, enforcement, and verifiability while minimizing new concepts, shared-root edits, manual registration, duplicate state, implicit exceptions, prose-only invariants, and human-only verification.

## Evidence boundary

L1 supplies domain facts and L2 supplies executable/assertion evidence. Evidence protects compilation, but evidence syntax should not dominate consumption. Claim IDs, receipts, schemas, manifests, and audit syntax remain sidecar concerns unless a Domain-rich consumer genuinely needs one as an executable primitive.

The rendered product may never state a stronger rule than the underlying evidence permits.

## Compression law

Shortening is allowed only when it does not remove a load-bearing invariant, exception, failure condition, or distinction whose absence changes plausible Best Path inference.

A shorter contract that creates a stronger unsupported instruction is worse than a longer self-contained one.
