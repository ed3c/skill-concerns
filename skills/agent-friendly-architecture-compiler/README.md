# Agent-Friendly Architecture Compiler

This Skill turns source-specific architecture evidence into a self-contained Agent contract that a zero-context coding LLM can use to infer the correct Best Path in an unfamiliar repository.

The Skill does not copy the vocabulary of the source system into the product. It extracts the architectural pressure, preserves the load-bearing semantics, and renders only concepts the consumer needs to make correct local decisions.

## Product boundary

The final product is the rendered Markdown contract. Compiler IR, evidence manifests, schemas, source-comparison matrices, and audit receipts exist to protect that product from drift; they are not part of the normal Agent reading path.

```text
source evidence + repository reality
        ↓
semantic kernel extraction
        ↓
BUILD candidate
        ↕
SHADOW review
        ↓
self-contained rendered contract
        ↓
zero-context Agent Best Path reasoning
```

## Two modes

### BUILD

BUILD is the only writing mode. It:

1. identifies the contributor-context assumptions;
2. extracts architecture invariants without source-specific black boxes;
3. separates universal semantic kernel from domain realization;
4. preserves failure/exception/negative knowledge that changes Best Path inference;
5. renders a short, direct contract with Context Model, Core Rules, Enforcement Hierarchy, Shortest Path, Greenfield, Slop, Rewrite, Architecture Addition, Implementation Procedure, and Best Path Decision Rule;
6. removes evidence machinery and unexplained source vocabulary from the hot path.

### SHADOW

SHADOW reads the same source evidence and BUILD candidate but does not write the implementation. It checks whether compression or generalization introduced a wrong inference.

Shadow findings use:

- `L0 OBSERVE` — possible issue, record only;
- `L1 WARN` — material ambiguity or evidence/semantic limitation;
- `L2 REVIEW` — candidate must be reconciled before publication because a zero-context Agent can reasonably infer a wrong Best Path.

SHADOW does not block for wording preference and does not become a second author.

## Three-layer product model

This Skill uses a separate three-layer product model from the Shadow intervention levels:

- **Product L0 — Semantic Kernel:** source-independent architectural pressures and invariants.
- **Product L1 — Self-contained Contract:** direct, fully defined Agent-facing rules with no required source-system knowledge.
- **Product L2 — Best Path Procedure:** executable decision procedure for choosing the smallest architecture-preserving, mechanically verifiable implementation path.

The product must remain understandable at L1/L2 without exposing compiler internals.

## Anti-overengineering law

A new layer, ontology, graph, registry, schema, or routing concept is justified only when it prevents a demonstrated failure that cannot be closed by strengthening the nearest existing boundary.

If a normal consumer must learn more concepts before making an ordinary change, the added layer is presumptively harmful.

## Evidence boundary

Evidence is required during compilation, but evidence syntax is not required in the rendered product. The renderer may omit claim IDs and authority labels from the hot path when their semantics have already been conservatively resolved.

The final text may never claim more than the underlying evidence supports. Unsupported generalization becomes narrower wording, explicit uncertainty, or omission—not invented universality.
