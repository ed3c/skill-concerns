# AGENTS.md — spatial-loop-grounded

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — provenance, receipt chain, hillclimb rule.
2. [`SKILL.md`](SKILL.md) — the eight grounded clauses in trigger form.
3. [`receipts.json`](receipts.json) — the exact provider receipts every clause binds to.
4. [`skill.json`](skill.json) — declared paths and executable route.
5. Read scripts, tests, and eval cases only when changing behavior.

## Stop laws

- A clause without a receipt binding does not enter this Skill, whatever its upstream quality.
- Receipts regenerate through their producers; hand-editing evidence is laundering.
- The upstream skills-shared body is the method owner; restating it here is drift, pointing at it is correct.
- Edits that weaken a trigger form, orphan a receipt, or erase provenance fail the validator; that is the hillclimb gate, not a formality.
- Session receipts prove one environment; portability claims require new receipts.

## Completion

Run `python3 skills/spatial-loop-grounded/scripts/validate_spatial_loop_grounded.py` and
`python3 -m unittest discover -s skills/spatial-loop-grounded/tests` from the repository root.
Report clause inventory, receipt bindings, and every hollow-mutation control outcome.
