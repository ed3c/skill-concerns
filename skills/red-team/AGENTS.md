# AGENTS.md — red-team

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — the one question, the roles, the curve.
2. [`SKILL.md`](SKILL.md) — clauses R1-R7, the catalogue contract, the diagnostics.
3. [`references/portable-falsification-kernel.md`](references/portable-falsification-kernel.md) — L0, one kernel per clause.
4. [`domain/catalogue.json`](domain/catalogue.json) — L1, the pinned classes with provenance, recipe and lifecycle.
5. [`domain/run-ledger.json`](domain/run-ledger.json) — L1, the append-only run records the curve reads.
6. [`scripts/shadow_driver.py`](scripts/shadow_driver.py) — L2, the toolkit, the boundary run, and the BUILD fold-in.
7. [`scripts/validate_red_team.py`](scripts/validate_red_team.py) — L2, the schemas, the ties, and the forbidden-surface scan.

## Stop laws

- Read the pinned catalogue before judging anything. A rule not in those bytes at that commit is not a rule this pass enforces.
- A catalogue match is a hypothesis. Report a class only with its experiment attached: exact subject, commands, expected, observed.
- Never write into a subject and never inject into a working agent. Experiments run in throwaway clones; the pass digests the subject before and after and refuses its own report if it moved.
- The driver files nothing. A provider-mutating verb in its bytes is `DRIVER_SURFACE_FORBIDDEN`, not a judgement call.
- A finding is a record the validator judges, not prose with a number. A record with no observed half is malformed.
- An escalation is one signal, for `irreversible-action-in-progress` or `runaway-resource-burn` only, carrying no instruction and no patch.
- The catalogue grows only from an adjudicated verdict and shrinks only when a gate lands. A gated class leaves active sampling; an active class with a landed gate is an error in the other direction.
- "No findings" is the honest and expected steady state. Report it as the result, never as a reason to look harder until something turns up.

## Completion

Run `python3 skills/red-team/scripts/validate_red_team.py`,
`python3 skills/red-team/scripts/validate_red_team.py --selftest`, and
`python3 -m unittest discover -s skills/red-team/tests`.
Report the tie results, the classes reproduced on the historical bundle, the
clean-bundle outcome, the round-trip fixture result, and this bundle's own
run-ledger record.
