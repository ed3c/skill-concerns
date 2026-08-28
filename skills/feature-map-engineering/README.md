# feature-map-engineering

Portable procedure for discovering, maintaining, and verifying software through actor-visible feature maps rather than implementation structure alone.

## Concern split

```text
SKILL.md
  decision policy, exploration boundary, verification laws

references/
  semantic schemas, coverage calculus, evidence contract, examples

../../contracts/feature-map.schema.json
  machine topology for one actor-visible capability

../../contracts/domain-adapter.schema.json
  consumer-owned bindings for drivers, commands, selectors, flags, runtime

scripts/feature_map.py
  executable semantic validator and coverage differ

scripts/validate_feature_map.py
  CLI adapter

scripts/coverage_diff.py
  CLI adapter

tests/ + evals/
  positive and planted negative controls
```

No product-specific driver is bundled. A consumer supplies a domain adapter and concrete assertions.

## Feature verification State Machine

```text
TASK_RECEIVED
→ ACTOR_INTENT_IDENTIFIED
→ FEATURE_MAP_LOCATED
   ├─ map present → MAP_BOUND
   └─ map absent  → PROVISIONAL_MAP
→ CHANGE_TO_FEATURE_EDGES_MAPPED
→ REQUIRED_JOURNEYS_DERIVED
→ PRODUCTION_EQUIVALENT_PATHS_EXECUTED
→ OBSERVABLE_EVIDENCE_COLLECTED
→ COVERAGE_RECONCILED
   ├─ reachable branch missing → CONTINUE
   ├─ dependency unavailable   → BLOCKED_RECORDED
   └─ required proof complete  → VERIFIED
→ MAP_UPDATED_IF_CONTRACT_CHANGED
```

Fail-closed states:

```text
FEATURE_IDENTITY_MISSING
ENTRY_POINT_DEAD
TRANSITION_INVALID
TERMINAL_WITHOUT_ORACLE
CHANGED_FEATURE_WITHOUT_JOURNEY
STATIC_ONLY_VERIFICATION
SKIP_WITHOUT_BLOCKER
PERSISTENCE_PROOF_MISSING
```

## Feature → proof DAG

```text
change
└─ affected feature
   ├─ entry-point journey A
   │  └─ observable proof
   ├─ entry-point journey B
   │  └─ observable proof
   └─ unreachable variant
      └─ blocker + nearest path + residual uncertainty
```

## Data flow

```text
behavioral docs + API/CLI help + acceptance tests + runtime observation
        ↓
FeatureMap IR
        ↓ states / transitions / terminals / observables
change surface + risk boundaries
        ↓
verification plan
        ↓ journeys + skips
domain adapter + execution driver
        ↓
runtime
        ↓
observable evidence
        ↓
meta-assertion engine
        ↓
VERIFIED / PARTIALLY_VERIFIED / BLOCKED / NOT_VERIFIED
```

## Machine interfaces

Validate a map and proof plan:

```bash
python3 skills/feature-map-engineering/scripts/validate_feature_map.py \
  --map skills/feature-map-engineering/fixtures/valid/feature-map.json \
  --plan skills/feature-map-engineering/fixtures/valid/verification-plan.json
```

Compare two map versions:

```bash
python3 skills/feature-map-engineering/scripts/coverage_diff.py \
  --old old-feature-map.json \
  --new new-feature-map.json
```

## Evidence ceiling

The bundled fixture and tests reach `L3_HERMETIC`: they execute real parser, graph, chain, coverage, evidence-boundary, persistence, skip, and mutation controls on exact local bytes.

They do not establish that an external Agent performs better on an unknown repository, that a consumer's domain adapter is correct, or that a production feature works.
