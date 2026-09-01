# AGENTS.md — arrival-engineering

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — the one question, the roles, and the three L-axes.
2. [`SKILL.md`](SKILL.md) — clauses A1-A6, the arrival vocabulary, the diagnostics.
3. [`references/portable-arrival-kernel.md`](references/portable-arrival-kernel.md) — L0, one kernel per clause.
4. [`domain/capability-topology.json`](domain/capability-topology.json) — L1, the audited rows and their receipts.
5. [`scripts/audit_islands.py`](scripts/audit_islands.py) — L2, the five-surface driver and the append refusal.
6. [`scripts/validate_arrival_engineering.py`](scripts/validate_arrival_engineering.py) — L2, the ties.

## Stop laws

- An audit that consulted one surface has measured declaration; report the surface set, never a verdict.
- A verb a consumer may remember to call is a planned island; bind it to an exit the consumer already traverses, and make the consumer's receipt inadmissible without it.
- A capability's recorded arrival is the highest one an actual receipt supports. Any claim above it is a finding, and levels rise only by receipt readback.
- A row without a resolvable receipt is refused at append. There are no aspirational rows.
- "Recorded in X" is unverified until X's bytes are opened and the exact value found.
- Unresolvable and unreachable are different states and never share a report shape.
- The closure law belongs to `context-closure-engineering`. Point at LAW-TRACE-GAP and LAW-NO-PROMOTION; a restated copy drifts from the copy under test.
- SHADOW has no write verb. A pass whose subject digest moved refuses its own report.

## Completion

Run `python3 skills/arrival-engineering/scripts/validate_arrival_engineering.py`,
`python3 skills/arrival-engineering/scripts/audit_islands.py --selftest`, and
`python3 -m unittest discover -s skills/arrival-engineering/tests`.
Report the tie results, the planted-island detection set, the negative-control
outcome, and this bundle's own recorded arrival level.
