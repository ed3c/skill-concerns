# Agent-Friendly Architecture Compiler

This Skill compiles evidence-backed architecture knowledge into a self-contained Agent contract that a zero-context coding LLM can use to infer the correct Best Path.

## The two Skill modes

The Skill has two product modes. This is the primary mode axis.

### 1. Domain-rich Skill

Use when repository/product-specific nouns are themselves load-bearing architecture primitives. The output may keep concrete domain vocabulary, paths, commands, owners, and execution surfaces, but every required concept must be defined in-place. Domain-rich must never mean hidden organizational knowledge.

### 2. Procedure-rich / Domain-decoupled Skill

Use when architecture knowledge should transfer across repositories. Remove source-system vocabulary and preserve the reusable semantic kernel: contributor context model, invariants, enforcement hierarchy, ownership, isolation, exceptions, failure learning, rewrite safety, and Best Path reasoning.

This is the default mode for a reusable Agent-Friendly Architecture contract.

## Skill concern stack — L0 / L1 / L2

`L0/L1/L2` are reserved for the standard Skill concern separation used by `skill-concerns`.

### L0 — PROCEDURAL SKILL

Portable, domain-independent decision policy.

Owns:
- extraction and compilation procedure;
- exploration policy;
- mode selection;
- semantic-preservation rules;
- Best Path reasoning policy;
- stop conditions and proof semantics.

For this Skill, the portable L0 implementation lives primarily in `SKILL.md` and reusable references.

### L1 — DOMAIN KNOWLEDGE

Concrete knowledge supplied by the consumer domain/repository.

May include:
- architecture primitives and vocabulary;
- capabilities and states;
- ownership/writer boundaries;
- entry points and extension surfaces;
- package/import constraints;
- feature flags and environment constraints;
- repository-specific failure modes and exceptions;
- evidence needed to distinguish real domain architecture from analogy.

In `DOMAIN_RICH` mode, selected L1 knowledge may survive into the rendered product when it is load-bearing and defined in-place. In `PROCEDURE_RICH_DOMAIN_DECOUPLED` mode, L1 is compilation input and should not leak source-specific black boxes into the reusable output.

### L2 — EXECUTION + ASSERTIONS

Concrete mechanisms that act, observe, assert, and persist evidence.

May include:
- repository analyzers;
- static checks;
- compiler/lint/CI gates;
- tests and drivers;
- runtime probes;
- negative controls;
- evidence persistence and readback.

L2 proves or falsifies domain realizations. It does not define portable procedure and must not silently become universal architecture semantics.

```text
L0 PROCEDURAL SKILL
        ↓ consumes
L1 DOMAIN KNOWLEDGE
        ↓ grounds
L2 EXECUTION + ASSERTIONS
```

This stack is about **where knowledge and authority live**, not about the shape of the rendered product.

## BUILD and SHADOW are roles, not modes or layers

Either Skill mode can use the same two execution roles:

```text
Domain-rich
  ├── BUILD
  └── SHADOW

Procedure-rich / Domain-decoupled
  ├── BUILD
  └── SHADOW
```

**BUILD** is the only writer. It owns evidence → semantic extraction → self-contained contract → Best Path.

**SHADOW** is read-only. It never creates a competing implementation. It reviews the same evidence/output for black-box vocabulary, semantic degradation, unsupported generalization, lost negative knowledge, authority laundering, and wrong Best Path inference.

To avoid collision with Skill L0/L1/L2, Shadow findings are named:

- `S0 OBSERVE` — record a non-load-bearing concern;
- `S1 WARN` — expose a material ambiguity or limitation;
- `S2 REVIEW` — publication must reconcile because the declared mode's consumer can reasonably infer a wrong Best Path.

## Rendered product compilation stack — P0 / P1 / P2

The rendered product has its own compilation stages. They are intentionally named `P0/P1/P2`, not L0/L1/L2.

### P0 — Semantic Kernel

Source-independent architecture pressure that must survive compression.

Examples: narrow-context Agents imitate local precedent; conventional paths should require fewer decisions than shortcuts; deterministic invariants belong at the strongest practical enforcement layer; durable truth should have one obvious writer.

### P1 — Self-contained Contract

Fully self-contained Agent-facing architecture language. Every concept required for correct Best Path reasoning is defined in-place.

A reusable domain-decoupled P1 must not require prior knowledge of the source project, its internal control plane, or compiler/evidence machinery.

### P2 — Best Path Procedure

Direct repository-change decision procedure derived from P1. It tells the consumer how to choose the smallest architecture-preserving and mechanically verifiable implementation path.

```text
Compilation input:
L0 procedure + L1 domain knowledge + L2 evidence
                  ↓
               P0 kernel
                  ↓
               P1 contract
                  ↓
               P2 Best Path
                  ↓
          rendered Markdown product
```

The two stacks are therefore orthogonal:

```text
Skill concern stack:      L0 Procedure → L1 Domain → L2 Execution/Assertions
Rendered product stack:   P0 Kernel    → P1 Contract → P2 Best Path
Review role severity:     S0 Observe   → S1 Warn     → S2 Review
```

## Product boundary

The final product is the rendered Markdown contract. Compiler IR, evidence manifests, schemas, comparison matrices, and audit receipts protect that product from drift but remain outside the normal Agent reading path unless a Domain-rich executable contract genuinely needs one.

## Anti-overengineering law

A new layer, ontology, graph, registry, schema, or routing concept is justified only when it prevents a demonstrated failure that cannot be closed by strengthening the nearest existing boundary.

If a normal consumer must learn more concepts before making an ordinary change, the added layer is presumptively harmful.

## Evidence boundary

Evidence is required during compilation, but evidence syntax is not required in the rendered product. The final text may never claim more than the underlying evidence supports. Unsupported generalization becomes narrower wording, explicit uncertainty, or omission—not invented universality.
