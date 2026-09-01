# Fixture context pack

> Authority ceiling: projection only. This pack cannot prove completion or
> authorize a transition. `[SRC-BRIEF, OWNER_REQUIREMENT, N]`

Snapshot ID: `FIXTURE-0123456-provider-19700101T000000Z`

## Frozen source denominator

| ID | Exact identity or pointer | Classification | Freshness and use |
|---|---|---|---|
| `SRC-BRIEF` | fixture owner order, digest `0000` | `OWNER_REQUIREMENT` | current task input |
| `SRC-TREE` | fixture commit `0123456789abcdef0123456789abcdef01234567` | `REPOSITORY_FACT` | exact baseline |
| `SRC-PROVIDER` | fixture provider readback at the snapshot time | `R_REFERENCE` | frozen provider denominator |
| `SRC-METHOD` | fixture pinned method bytes | `METHOD_SOURCE` | procedure, not correctness |
| `SRC-PAPER` | fixture article; bytes, URL, and hash unavailable | `EXTERNAL_CLAIM` plus `ABSENT` | not verified here |

Every row stays in the denominator once entered. `[SRC-BRIEF, OWNER_REQUIREMENT, N]` `[SRC-TREE, REPOSITORY_FACT, N]`

## Update rules

1. Freeze one exact commit and one timestamped provider denominator. `[SRC-BRIEF, OWNER_REQUIREMENT, N]`
2. Unavailable sources stay absent instead of disappearing. `[SRC-PAPER, EXTERNAL_CLAIM plus ABSENT, N]`
3. Pinned methods stay procedure and never become evidence. `[SRC-METHOD, METHOD_SOURCE, P]`
4. Re-read mutable provider facts before acting on them. `[SRC-PROVIDER, R_REFERENCE, N]`
