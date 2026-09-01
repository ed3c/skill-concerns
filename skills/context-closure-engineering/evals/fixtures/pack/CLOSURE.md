# Fixture problem closure matrix

## Closure vocabulary

| State | Meaning |
|---|---|
| `CLOSED_BOUNDED` | the narrow named denominator has an exact pointer and no known residual |
| `PARTIAL` | material atoms exist, a wider denominator stays open |
| `OPEN` | an owner exists, completion evidence is absent |
| `UNOWNED` | no exact object in the source set owns the gap |

A merged commit closes only the denominator its evidence lane covers. `[SRC-PROVIDER, R_REFERENCE, N]`

## Owner problem matrix

| ID | Source problem | Exact owner | Projection | Residual |
|---|---|---|---|---|
| `P-PACK-001` | recover the program without the latest prompt | node-b | `PARTIAL` | raw conversation absent |
| `P-SOURCE-001` | account for article and PDF identity | none | `UNOWNED` | bytes and hashes unavailable |

Each row names its denominator, owner, and residual. `[SRC-BRIEF, OWNER_REQUIREMENT, N]` `[SRC-PAPER, EXTERNAL_CLAIM plus ABSENT, N]`

## Closure laws

1. A closed object whose marker disagrees does not satisfy a typed dependency. `[SRC-PROVIDER, R_REFERENCE, N]`
2. A merged commit proves ancestry, not runtime behavior. `[SRC-TREE, REPOSITORY_FACT, N]`
3. Local, trusted, provider, and human lanes do not substitute for one another. `[SRC-METHOD, METHOD_SOURCE, P]`
