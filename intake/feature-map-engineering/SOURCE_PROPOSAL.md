# Source proposal — feature-map-engineering

Owner-provided design brief, materialized for content-bound admission.

## Load-bearing design rules

1. A Skill is a decision policy and operating contract, not a long product wiki or click macro.
2. Feature maps describe actor-visible capabilities, states, entry points, variants, failure paths, and observable assertions rather than implementation structure.
3. Procedure, domain knowledge, execution mechanics, feature topology, and evidence are separate concerns.
4. The generic procedure decides **how** to discover and verify; a domain adapter declares **with what**; a feature map declares **what**; executable assertions declare **proof**.
5. `VERIFIED` is an evidence state. Static code inspection, handler execution, a mock, or a unit test alone cannot prove an externally observable capability.
6. Skipped or unreachable paths retain uncertainty and must name their blocker.
7. Feature maps should model behavioral state transitions, not screenshot inventories.
8. Markdown owns semantics, machine-readable IR owns topology, and code owns mechanics.
9. Generic scripts enforce meta-assertions rather than product-specific selectors.
10. Hard invariants, soft conventions, domain contracts, and incidental discoverable facts must not be collapsed into one prompt.
11. Feature Map and Code Map remain separate graphs connected by explicit mappings.
12. Change → Feature → Journey → Proof is the acceptance DAG.
13. Runtime reality beats stale documentation; the map must be repaired when the observable contract changes.
14. A portable Skill preserves exploration space and does not pre-decide selectors, commands, components, endpoints, or architectures.
15. A domain-heavy Skill may be concrete only when its adapter and runtime assertions are physically verified.

## Intended first bundle

```text
feature-map-engineering/
├── SKILL.md
├── references/
├── scripts/
├── tests/
└── evals/
```

The first admission implements FeatureMap IR, a domain-adapter schema, coverage reconciliation, evidence rules, skip semantics, and executable meta-assertions with planted negative controls.

## External design reference

The owner brief cited the Maven page for Lauren Schaefer's discussion of verification skills, feature maps, eval maintenance, local-to-cloud verification, strict CI, and agent-optimized architecture:

https://maven.com/p/e23d9c/how-cursor-turned-ai-agents-into-better-engineers

This URL is a design reference, not runtime evidence and not a copy of any private `control-glass` source.
