# Fixture drift and omission ledger

## Intervention severities

This bundle also uses `L` for the evidence-ceiling axis (`L0_SOURCE_FREEZE`
through `L3_HERMETIC`) and for the authority axis (`L`/`R` promoted classes).
Severity below is a third, unrelated axis, so it is spelled `SEV-*` rather than
reusing `L0`-`L3` for a third meaning.

| Severity | Meaning |
|---|---|
| `SEV-0 OBSERVE` | record a material fact |
| `SEV-1 WARN` | work may continue within an explicit ceiling |
| `SEV-2 REVIEW` | reconcile before depending on it |
| `SEV-3 BLOCK` | continuing risks identity, authority, writer, or evidence corruption |

Severity is not an execution or completion verdict. `[SRC-METHOD, METHOD_SOURCE, P]`

## Findings

`DRIFT-F01` at `SEV-3 BLOCK`: node-c is closed while its marker disagrees, so
its dependents cannot read it as landed. `[SRC-PROVIDER, R_REFERENCE, N]`

`DRIFT-F02` at `SEV-2 REVIEW`: the article source has no addressable identity,
so its claim mapping stays open. `[SRC-PAPER, EXTERNAL_CLAIM plus ABSENT, N]`

## Mandatory review checklist

- Does every source family stay present, historical, unknown, or absent?
- Does every nontrivial statement name a source and a classification?
- Are start and completion edges separate?
- Does each active write boundary have one convergence owner?
- Does any projection path appear in an evidence field?

Each answer names a source id and classification. `[SRC-BRIEF, OWNER_REQUIREMENT, N]`
