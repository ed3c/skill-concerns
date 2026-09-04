# Agent-Friendly Architecture Compiler

This Skill compiles evidence-backed architecture knowledge into a self-contained Agent contract that a zero-context coding LLM can use to infer the correct Best Path.

## The two Skill modes

### 1. Domain-rich Skill
Use when repository/product-specific nouns are themselves load-bearing architecture primitives. Every required domain concept must be defined in-place; Domain-rich must never mean hidden organizational knowledge.

### 2. Procedure-rich / Domain-decoupled Skill
Use when architecture knowledge should transfer across repositories. Remove source-system vocabulary and preserve the reusable architecture semantics required for correct Best Path reasoning.

## Skill concern stack — L0 / L1 / L2

`L0/L1/L2` are reserved for the `skill-concerns` ownership stack:

- **L0 — PROCEDURAL SKILL:** portable decision policy, exploration, semantic-preservation rules, stop conditions, proof semantics.
- **L1 — DOMAIN KNOWLEDGE:** capabilities, states, owners/writers, entry points, extension surfaces, selectors/flags, environment constraints, exceptions.
- **L2 — EXECUTION + ASSERTIONS:** analyzers, scripts, tests, drivers, runtime probes, negative controls, assertions, evidence persistence/readback.

L2 may prove or falsify a domain realization; it must not silently become universal architecture semantics.

## BUILD and SHADOW are roles

Both Skill modes can use:

```text
Domain-rich                         Procedure-rich / Domain-decoupled
  ├── BUILD                           ├── BUILD
  └── SHADOW                          └── SHADOW
```

**BUILD** is the only writer. **SHADOW** is read-only and checks black-box vocabulary, semantic degradation, unsupported generalization, lost negative knowledge, authority laundering, and wrong Best Path inference.

Shadow severity is separate from Skill layers:

- `S0 OBSERVE`
- `S1 WARN`
- `S2 REVIEW`

## Compilation stages — C0 / C1 / C2

`C` means **Compilation**. These names describe transformation stages of the rendered product and do not overlap with priority labels or the `P/L/R/N` evidence vocabulary.

### C0 — Semantic Kernel
Source-independent architecture pressure that must survive domain removal and compression.

**Question:** What survives domain removal?

### C1 — Self-contained Contract
Fully defined Agent-facing architecture language. Every concept required for Best Path reasoning is explained in-place.

**Question:** What must the Agent understand?

### C2 — Best Path Procedure
Direct repository-change decision procedure derived from C1. It tells the Agent how to choose the smallest architecture-preserving, mechanically verifiable implementation path.

**Question:** What should the Agent do?

```text
L0 procedure + L1 domain knowledge + L2 execution/assertions
                         ↓
                  C0 Semantic Kernel
                         ↓
              C1 Self-contained Contract
                         ↓
                C2 Best Path Procedure
                         ↓
                  Rendered Markdown
                         ↓
                  zero-context Agent
```

The namespaces are intentionally orthogonal:

```text
Skill concern stack:   L0 → L1 → L2
Compilation stages:    C0 → C1 → C2
Shadow severity:       S0 → S1 → S2
Execution roles:       BUILD | SHADOW
Skill modes:           DOMAIN_RICH | PROCEDURE_RICH_DOMAIN_DECOUPLED
```

## Product boundary

The final product is the rendered Markdown contract. Compiler IR, evidence manifests, schemas, comparison matrices, and audit receipts protect the product but remain outside the normal Agent reading path unless a Domain-rich executable contract genuinely requires one.

## Anti-overengineering law

A new layer or ontology is justified only when it prevents a demonstrated failure that the nearest existing boundary cannot close. If a normal consumer must understand more concepts before an ordinary change, the added layer is presumptively harmful.
