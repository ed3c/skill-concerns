# agent-friendly-architecture-compiler — pre-guard fixture material

Frozen inputs retargeted from `ed3c/ai-content-notes` PR #77 (branch
`agent/noodles-agent-friendly-fixture`, head `c461dd5e30630597b061dd6ad9ce5f4512bd3e49`).
That PR was never merged; these bytes never reached `ai-content-notes` `main`.

These files are **pre-guard**. They predate the compiler's rendered-contract guard and are
kept here as fixture material only. Nothing in this directory is an admitted Skill, a
compliant render, or a source lock.

## Files

| File | Role | Source blob |
|---|---|---|
| `agent-friendly-architecture.md` | Red corpus: the pre-guard render template. Output shaped by it fails the rendered-contract guard. | `55dc00ac6912b229ff65e28e1004743dda56712f` |
| `architecture-context-pack.schema.json` | Compile-input schema: the machine contract for the Context Pack the compiler consumes. Not guarded output. | `3b36d9e85fda88eb94b9917be28234f48cf4dfeb` |

Both blobs are byte-identical to their PR #77 originals (`git hash-object` on the copies
reproduces the source blob SHAs above). The machine-checkable record of that identity is
`../source-lock.json` (schema per `contracts/source-lock.schema.json`, same shape every other
`intake/*` directory uses); this table is the human-readable summary, not the source of truth.

## Red-corpus receipt

`skills/agent-friendly-architecture-compiler/scripts/validate_rendered_contract.py`
(candidate branch `agent/agent-friendly-architecture-compiler`) run against
`agent-friendly-architecture.md`:

```text
exit=1, 22 findings
  10x missing required heading (all of ## Context Model .. ## Best Path Decision Rule)
   2x rendered hot path leaks black-box/compiler vocabulary (evidence-manifest.json, authority_ceiling)
   9x load-bearing Best Path semantic missing
   1x rendered product exposes evidence/compiler machinery in the hot path
```

The guard is a negative control: this template must stay red. If a change makes it green,
either the template stopped being the pre-guard artifact or the guard stopped rejecting.

**This is not currently self-enforcing.** `scripts/run_all.py` on this branch never calls
`validate_rendered_contract.py` — that script lives only on the un-merged draft branch
`agent/agent-friendly-architecture-compiler` (head `4d27bfa4edc34b32b4b088fd3df0b40ab2a420c0`
at the time this fixture material was frozen). Nothing in this repository today would go red
if the template above were edited to pass. The guard becomes self-enforcing only once issue
#19 lands the compiler and its guard under `skills/`; until then the `exit=1, 22 findings`
receipt above is a one-time snapshot, reproducible only by re-running that script against that
branch while it still exists at that SHA, not a standing check.

## Non-claims

- This is not an admission receipt and grants no admission.
- The schema is a compile **input** contract; it says nothing about whether a render passes.
- The template is not a specification of the compiler's product; the product contract lives
  with the candidate Skill.
- No claim is made that any render derived from this template has ever passed the guard.
- The schema's `$id` (`https://github.com/ed3c/ai-content-notes/schemas/...`) is a frozen byte
  of the PR #77 original, not a live or resolvable URI — this directory holds frozen source
  identities only (`../README.md`), so it is not rewritten to a `skill-concerns` URL here.
  Whatever repository formally adopts this schema under issue #19 owns re-authoring `$id`.
