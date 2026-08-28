# AGENTS.md — feature-map-engineering

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — ownership, State Machine, DAG, data flow, evidence ceiling.
2. [`SKILL.md`](SKILL.md) — portable decision policy and stop laws.
3. [`skill.json`](skill.json) — declared concern split and executable routes.
4. [`references/README.md`](references/README.md) — select only the reference needed for the task.
5. Shared [`feature-map.schema.json`](../../contracts/feature-map.schema.json) and [`domain-adapter.schema.json`](../../contracts/domain-adapter.schema.json) when shaping machine contracts.
6. `scripts/`, `tests/`, `evals/cases.json`, and exact fixture/issue/PR subjects when changing behavior.

## Writer and concern rules

- Keep product/repository selectors, commands, endpoints, flags, account state, and environment setup out of the portable core.
- A consumer domain adapter supplies those bindings.
- Markdown explains semantics; JSON owns topology; Python owns validation mechanics.
- Add a planted negative control whenever a new semantic rule could otherwise pass hollow.
- Do not weaken a control to make a candidate pass.
- A skipped path is not verified.
- `VERIFIED` requires production-equivalent observable evidence.
- Keep `L4_MATCHED_LIVE_RUNTIME` and `L5_DELIVERY_AND_PRODUCTION` unclaimed without separate exact receipts.

## Completion

Run:

```bash
python3 scripts/run_all.py
```

Report changed feature contracts, changed meta-assertions, positive and negative cases, exact evidence ceiling, and all residual uncertainty.
