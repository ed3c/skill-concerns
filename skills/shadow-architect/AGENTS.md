# AGENTS.md — shadow-architect

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — the one question, the roles, why every clause carries a real judged diff.
2. [`SKILL.md`](SKILL.md) — clauses P1-P7, the ledger contract, the diagnostics.
3. [`references/portable-architecture-policy.md`](references/portable-architecture-policy.md) — L0, one kernel per clause, domain-free.
4. [`domain/precedents.json`](domain/precedents.json) — L1, the pinned precedents with provenance, detector, fixture and control.
5. [`scripts/shadow_driver.py`](scripts/shadow_driver.py) — L2, the reader-only pass, the finding schema's emitter, and the BUILD fold-in.
6. [`scripts/validate_shadow_architect.py`](scripts/validate_shadow_architect.py) — L2, the schemas, the ties, the reach scan.

## Stop laws

- Read the pinned ledger before judging anything. A principle not in those bytes at that commit is not a principle this pass applies.
- A signal is a question, never a verdict. Report a clause only with the added bytes that raised it quoted, and let the person who wrote the change answer it.
- Detection reads ADDED lines only, and so does acquittal. Unchanged context that mentions the right word does not exculpate a shape the diff introduces.
- Never write into a subject. The pass digests the subject before and after and refuses its own report if it moved.
- The bundle files nothing and runs nothing. A module here that imports a way to spawn a process or open a socket is `DRIVER_SURFACE_FORBIDDEN`, not a judgement call.
- No experiments. Falsification belongs to the sibling that owns that verb; asking is this one's whole job.
- The ledger grows only from an adjudicated verdict. A clause is an enforcement shape, so a fold-in with no cure-authorization is refused, and a detection never authorizes the clause it detects.
- "No findings" is the honest and expected steady state. Report it as the result, never as a reason to keep looking until something turns up.

## Completion

Run `python3 skills/shadow-architect/scripts/validate_shadow_architect.py`,
`python3 skills/shadow-architect/scripts/validate_shadow_architect.py --selftest`,
and `python3 -m unittest discover -s skills/shadow-architect/tests`.
Report the tie results, the clauses reproduced on the historical wave diff with
the bytes they quoted, both planted-arm outcomes against the answer key, and the
provenance readback for every clause.
