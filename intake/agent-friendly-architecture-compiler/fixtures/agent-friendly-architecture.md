# Agent-Friendly Architecture — rendered context template

> This is the human-facing projection of an evidence-bound Architecture Context Pack. Keep it short. Do not duplicate the evidence database here.

## Contributor context

{{contributor_context}}

## Design objective

**{{design_objective}}**

Unsafe shortcuts should fail at the strongest available deterministic boundary with a diagnostic that names the supported path.

## Architecture contract

{{#invariants}}
{{ordinal}}. **{{title}}** — {{statement}}
{{/invariants}}

## Architecture carriers

{{#carriers}}
- **{{name}}** → {{responsibility}}. Carries: {{invariant_refs}}.
{{/carriers}}

## Enforcement

{{#claims}}
- **{{claim_id}}** — {{rendered_claim}} `[{{authority_ceiling}}]`
{{/claims}}

`P/N` evidence must never be rendered as deterministic or provider-enforced truth. A claim may be rendered no stronger than its strongest bound evidence.

## Divergence and limits

{{#divergences}}
- {{statement}}
{{/divergences}}

## Do not infer

{{#negative_claims}}
- {{statement}}
{{/negative_claims}}

## Best Path

{{best_path}}

## Evidence lookup

For every material claim above, resolve `claim_id` in the sibling `evidence-manifest.json`. The manifest binds source/repository revision, exact locator, evidence kind, authority ceiling, and—when claimed—implementation/test/negative-control/runtime or provider receipts.

If a material claim has no valid manifest entry, render it as `UNKNOWN` or omit it. Never repair a missing evidence binding by analogy, semantic similarity, model consensus, or prose repetition.
