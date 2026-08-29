# skill-concerns

`skill-concerns` is a curated distribution repository for **physically admitted Agent Skills**.

Source repositories may incubate large, mixed, or domain-heavy Skills. This repository accepts a refactored bundle only when its concern boundaries and proof routes are machine-checkable. The first bundle is [`feature-map-engineering`](skills/feature-map-engineering/README.md).

## Repository role

```text
source repository / owner design brief
        ↓ freeze exact bytes
probabilistic concern extraction and refactor
        ↓
candidate Skill bundle
        ↓ deterministic structure + route gates
executable mechanisms + positive/negative controls
        ↓ hermetic evaluation
content-bound admission receipt
        ↓ exact-head hosted check
main: admitted distribution
        ↓
consumer repository chooses and binds domain adapter
```

This repository is not a product runtime, secret store, worktree manager, provider session, or production evidence database.

## Directory map and ownership

```text
AGENTS.md
  repository procedure, stop laws, Golden Path, evidence boundary

agents-routing.json
  complete three-document Agent routing graph

registry.json
  admitted Skill inventory and minimum evidence policy

contracts/
  shared machine-readable shapes

intake/
  frozen design briefs or Git source locks; never runtime state

admissions/
  content-bound receipts for complete admitted Skill trees

skills/
  admitted bundles only
  └── <skill>/
      ├── AGENTS.md       third and final Agent contract
      ├── README.md       local topology, State Machine, DAG, data flow
      ├── SKILL.md        portable decision policy
      ├── skill.json      concern split and executable routes
      ├── references/     reusable semantics
      ├── scripts/        deterministic mechanisms
      ├── tests/          positive and negative controls
      └── evals/          machine case inventory

scripts/
  repository promotion gates

tests/
  planted repository-level falsifiers

.github/workflows/
  read-only exact-head execution
```

## Admission State Machine

```text
PROPOSED
→ SOURCE_LOCKED
→ REFACTORED
→ STRUCTURAL_PASS
→ EXECUTABLE_PASS
→ HERMETIC_PASS
→ RECEIPT_BOUND
→ PR_CHECKED
→ ADMITTED
```

Fail-closed terminals include:

```text
SOURCE_ABSENT
AGENT_ROUTE_TOO_DEEP
AGENT_ROUTE_CYCLE
BUNDLE_INCOMPLETE
DOMAIN_LEAKAGE
DEAD_OR_HOLLOW_ROUTE
TERMINAL_WITHOUT_ORACLE
STATIC_ONLY_VERIFICATION
SKIP_WITHOUT_BLOCKER
RECEIPT_DRIFT
EVIDENCE_PROMOTION
```

## Work DAG

```text
source lock
├─ three-document Agent route
├─ Skill anatomy and concern classification
├─ executable route reachability
└─ feature/proof contracts
   ├─ positive executable journey
   ├─ missing-oracle mutation
   ├─ static-only false-proof mutation
   ├─ skip-without-blocker mutation
   └─ dead/hollow route mutation
      ↓
complete tree digest + admission receipt
      ↓
hosted exact-head verification
```

The branches above are proof dependencies, not invented Git ancestry. One PR may contain the initial bootstrap because the repository started empty; future unrelated Skill admissions should remain path-disjoint sibling PRs.

## Data flow

```text
owner brief or source checkout
        ↓
intake/<skill>/SOURCE_PROPOSAL.md or frozen Git tree
        ↓ sha256 source lock
candidate portable core + optional domain adapter + execution code
        ↓
registry + manifest + schemas
        ↓
repository and Skill validators
        ↓
positive/negative eval denominator
        ↓
admissions/<skill>.json
        ↓ exact file and contract hashes
GitHub pull-request head
        ↓ read-only workflow
eligible main content
```

## Current admitted inventory

| Skill | Kind | Evidence ceiling | What is proven | Not proven |
|---|---|---:|---|---|
| `feature-map-engineering` | `procedure-rich` | `L3_HERMETIC` | anatomy, concern split, FeatureMap IR semantics, executable meta-assertions, positive and planted negative controls | matched live-agent uplift, product-specific adapter correctness, consumer integration, production behavior |
| `control-noodle` | `composed` | `L3_HERMETIC` | exact procedure/domain composition, separate Feature and Code Maps, explicit mapping, change-to-journey compilation, and planted boundary/evidence mutations | live Noodle operation, upstream Issues #19/#20, provider landing, consumer integration, production behavior |

Mutable hosted check status is read from the current commit/PR rather than copied into this README.

## Local verification

```bash
python3 scripts/run_all.py
```

The suite uses the Python standard library only. It checks the repository graph, every admitted bundle, complete content identities, the first Skill's executable contracts, and planted falsifiers.

## Importing from `skills-shared` or another repository

Read [`docs/IMPORTING.md`](docs/IMPORTING.md). The source is frozen at an exact commit and path before refactoring. `skill-concerns` imports no branch names, worktrees, provider sessions, credentials, or live receipts. A new candidate must earn its own admission receipt under this repository's smaller concern contract.

## Evidence ceiling

A green repository suite establishes `L3_HERMETIC` only for the exact bundled mechanisms and fixtures it executes. It does not establish `L4_MATCHED_LIVE_RUNTIME` or `L5_DELIVERY_AND_PRODUCTION`.
