# AGENTS.md — agent-friendly-architecture-compiler

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. `README.md` — mode/namespace/product boundary.
2. `SKILL.md` — portable compilation and Shadow-review procedure.
3. `skill.json` — declared anatomy and executable route.
4. `references/product-contract.md` — rendered-product requirements.
5. Read scripts, tests, and evals only when changing behavior or proving the bundle.

## Namespace law

Do not overload layer names:

```text
L0/L1/L2 = Skill concern stack
C0/C1/C2 = Compilation stages
S0/S1/S2 = SHADOW severity
BUILD/SHADOW = execution roles
DOMAIN_RICH / PROCEDURE_RICH_DOMAIN_DECOUPLED = Skill modes
```

`C` means Compilation. Never rename C0/C1/C2 to P0/P1/P2: `P` is commonly interpreted as priority and may collide with `P/L/R/N` evidence vocabularies.

## Product invariant

The final C1/C2 rendered architecture contract must be understandable by the consumer defined by the selected Skill mode without hidden source-framework, repository, evidence-ontology, or compiler knowledge.

- In `PROCEDURE_RICH_DOMAIN_DECOUPLED`, source-specific control-plane vocabulary must not leak into the portable product.
- In `DOMAIN_RICH`, a domain primitive may remain only when it is Best-Path-critical and defined in-place with ownership, constraints, allowed operations, and decision consequence.

## Execution roles

- **BUILD** — sole writer; consumes L0/L1/L2 inputs and produces C0 → C1 → C2.
- **SHADOW** — read-only reviewer; never creates a competing implementation.

SHADOW checks black-box vocabulary, semantic degradation, unsupported generalization, lost negative knowledge, authority laundering, and wrong Best Path inference.

## Shadow severity

- **S0 OBSERVE** — record a non-load-bearing concern.
- **S1 WARN** — expose a material ambiguity or narrower safe interpretation.
- **S2 REVIEW** — reconcile before publication when a consumer can plausibly infer a wrong Best Path.

Do not use S2 for style preference.

## Stop laws

- Do not produce a source-system summary when the task requires reusable architecture guidance.
- Do not make schemas, manifests, claim IDs, evidence enums, graph systems, or compiler machinery part of the normal Agent hot path unless a Domain-rich executable primitive truly requires one.
- Do not generalize an L1/L2 domain realization into C0 solely because it exists or passes a local test.
- Do not remove divergence, exceptions, failure modes, or negative knowledge when that loss could strengthen or reverse the Best Path inference.
- Do not add a conceptual layer unless it prevents a demonstrated failure that the nearest existing boundary cannot close.

## Completion

Run the validator and tests declared in `skill.json`. Report the selected Skill mode, L0/L1/L2 inputs exercised, C0/C1/C2 product checks, SHADOW S0/S1/S2 findings, planted negative-control results, and exact evidence ceiling reached.
