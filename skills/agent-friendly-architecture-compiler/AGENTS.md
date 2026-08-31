# AGENTS.md — agent-friendly-architecture-compiler

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. `README.md` — product boundary and two-mode model.
2. `SKILL.md` — portable compilation and shadow-review procedure.
3. `skill.json` — declared anatomy and executable route.
4. `references/product-contract.md` — self-contained rendered-product requirements.
5. Read scripts, tests, and evals only when changing behavior or proving the bundle.

## Product invariant

The final rendered architecture contract must be understandable by a zero-context coding LLM without requiring prior knowledge of the source framework, source repository, evidence ontology, compiler internals, or comparison fixture.

Source-specific nouns may appear only when they are themselves necessary architectural primitives in the target contract and are defined in-place. A source project's control-plane vocabulary must never leak into the portable product merely because it was useful as evidence during extraction.

## Two modes

- **BUILD** — compile evidence-backed architecture knowledge into one self-contained Agent-facing contract that directly supports Best Path reasoning.
- **SHADOW** — read the same inputs and candidate output as a non-writing architecture reviewer. Detect black-box vocabulary, semantic degradation, unsupported generalization, lost negative knowledge, authority laundering, and additional cognitive layers that make the Best Path harder to infer.

SHADOW is never a second implementation writer.

## Shadow levels

- **L0 OBSERVE** — record a possible issue without changing the candidate or stopping BUILD.
- **L1 WARN** — expose a material ambiguity, evidence ceiling, black-box dependency, or likely Best Path misread while BUILD may continue.
- **L2 REVIEW** — require architecture/context reconciliation before the next major publication checkpoint when the rendered product is not self-contained, loses a load-bearing invariant, or can plausibly drive a wrong Best Path.

Do not use L2 for style preference, wording taste, or harmless domain-specific detail.

## Stop laws

- Do not produce a domain-flavored summary when the task is a reusable Agent contract.
- Do not require the consumer to understand the source project before understanding the architecture.
- Do not make schema, evidence manifest, claim IDs, authority enums, FeatureMap, or other compiler machinery part of the ordinary Agent reading path.
- Do not generalize a source-specific mechanism into a universal rule unless the semantic kernel survives without the source noun and the evidence supports that abstraction.
- Do not delete divergence, exception, failure, or negative knowledge when its loss could produce a stronger or wrong Best Path inference.
- Do not add a new conceptual layer unless it prevents a demonstrated failure that the nearest existing contract cannot close.

## Completion

Run the validator and unit tests declared in `skill.json`. Report BUILD output checks, SHADOW L0/L1/L2 findings, planted negative-control results, and the exact evidence ceiling reached by this Skill bundle.
