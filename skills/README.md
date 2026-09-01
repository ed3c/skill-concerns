# Admitted Skills

| Skill | Kind | Purpose | Evidence ceiling |
|---|---|---|---:|
| [`feature-map-engineering`](feature-map-engineering/README.md) | `procedure-rich` | Discover, model, and verify actor-visible behavior through FeatureMap IR and executable meta-assertions | `L3_HERMETIC` |
| [`control-noodle`](control-noodle/README.md) | `composed` | Bind the feature-map procedure to a source-frozen Noodles control pack, separate Code Map, explicit mapping, and change-to-journey compiler | `L3_HERMETIC` |
| [`spatial-loop-grounded`](spatial-loop-grounded/README.md) | `domain-rich` | Supervise a grounded loop's actors against measured campaign evidence rather than reported outcomes | `L3_HERMETIC` |
| [`control-code-intel`](control-code-intel/README.md) | `domain-rich` | Control the physically-verified code-intelligence stack across one or many repositories | `L3_HERMETIC` |
| [`control-backup`](control-backup/README.md) | `domain-rich` | Control the physically-verified snapshot backup stack, including the tiers it dropped on measured loss | `L3_HERMETIC` |
| [`context-closure-engineering`](context-closure-engineering/README.md) | `domain-rich` | Compile long mixed source material into one bounded projection - denominator, DAG, closure, traceability, drift - and check that projection mechanically | `L3_HERMETIC` |
| [`dynamic-workflow`](dynamic-workflow/README.md) | `domain-rich` | Read a dispatch runtime and classify its lanes - complete, healthy, stalled-suspect, dead - across Claude Code Workflow waves and codex daemon sessions | `L3_HERMETIC` |

This table is a reader's index kept in sync by `scripts/check_skill_bundles.py` (`SKILL_INDEX_ROW_ABSENT` / `SKILL_INDEX_ROW_KIND_DRIFT`, ed3c/skill-concerns#74): `registry.json` is still the admitted inventory, and a Skill entry is not admitted by a row here or by directory presence -- but this row can no longer drift from the admitted set silently. `registry.json`, its manifest, source lock, admission receipt, scripts, tests, and eval inventory form one content-bound subject.
