# Agent-Friendly Architecture Compiler

This Skill compiles evidence-backed architecture knowledge into a self-contained Agent contract that a zero-context coding LLM can use to infer the correct Best Path.

## The two Skill modes

The Skill has two product modes. This is the primary mode axis.

### 1. Domain-rich Skill

Use when repository/product-specific nouns are themselves load-bearing architecture primitives. The output may keep concrete domain vocabulary, paths, commands, owners, and execution surfaces, but every required concept must be defined in-place. Domain-rich must never mean hidden organizational knowledge.

### 2. Procedure-rich / Domain-decoupled Skill

Use when the architecture knowledge should transfer across repositories. Remove source-system vocabulary and preserve the reusable semantic kernel: contributor context model, invariants, enforcement hierarchy, ownership, isolation, exceptions, failure learning, rewrite safety, and Best Path reasoning.

This is the default mode for a reusable Agent-Friendly Architecture contract.

## BUILD and SHADOW are roles, not modes

Either Skill mode can use the same two execution roles:

```text
Domain-rich
  ├── BUILD
  └── SHADOW

Procedure-rich / Domain-decoupled
  ├── BUILD
  └── SHADOW
```

**BUILD** is the only writer. It owns evidence → semantic kernel → self-contained contract → Best Path.

**SHADOW** is read-only. It never creates a competing implementation. It reviews the same evidence/output for black-box vocabulary, semantic degradation, unsupported generalization, lost negative knowledge, authority laundering, and wrong Best Path inference.

SHADOW intervention levels are:

- `L0 OBSERVE` — record a non-load-bearing concern;
- `L1 WARN` — expose a material ambiguity or limitation;
- `L2 REVIEW` — publication must reconcile because the declared mode's consumer can reasonably infer a wrong Best Path.

## Product layers

These are separate from SHADOW's intervention levels:

- **L0 — Semantic Kernel:** load-bearing architecture pressure that must survive compression.
- **L1 — Self-contained Contract:** every concept required for correct reasoning is defined in the output.
- **L2 — Best Path Procedure:** direct repository-change decision procedure.

For Domain-decoupled output, a zero-context LLM must not need Dune, Noodle, noodles, P/L/R/N, FeatureMap, Spatial Loop, or compiler internals. For Domain-rich output, the consumer may use domain vocabulary only when the output defines why each primitive exists and how it changes the Best Path.

## Product boundary

The final product is the rendered Markdown contract. Compiler IR, evidence manifests, schemas, comparison matrices, and audit receipts protect that product from drift but remain outside the normal Agent reading path unless a Domain-rich executable contract genuinely needs one.

```text
source evidence + repository reality
        ↓
select Skill mode
        ↓
BUILD semantic kernel + contract + Best Path
        ↕
SHADOW L0/L1/L2 review
        ↓
self-contained rendered contract
        ↓
Agent Best Path reasoning
```

## Anti-overengineering law

A new layer, ontology, graph, registry, schema, or routing concept is justified only when it prevents a demonstrated failure that cannot be closed by strengthening the nearest existing boundary.

If a normal consumer must learn more concepts before making an ordinary change, the added layer is presumptively harmful.

## Evidence boundary

Evidence is required during compilation, but evidence syntax is not required in the rendered product. The final text may never claim more than the underlying evidence supports. Unsupported generalization becomes narrower wording, explicit uncertainty, or omission—not invented universality.
