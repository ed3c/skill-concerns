# spatial-loop-grounded

The environment-evidenced subset of `skills-shared/skills/spatial-loop-systems-engineering`.

Upstream owns the method (registry status: method ownership only, live receipts
environment-owned). This skill owns the twelve clauses that survived physical
contact — the ed3c/noodles machine sessions of 2026-08-30/31, one
host-scheduler receipt (a second environment class), and one cross-repository
pair from 2026-09-01 — each bound to exact receipts in `receipts.json` and
guarded by hollow-mutation evals (`evals/cases.json`, run via `tests/`).
Clause fixtures under `evals/clause-fixtures/` carry the hermetic half of
judging a clause: each is an artifact its clause is about, and the validator
computes the verdict from its bytes rather than reading the fixture's name.

Three skill-concern layers, one method (distinct from the Compilation stages
C0/C1/C2 and from Shadow severity S0/S1/S2 — never mix the namespaces):
- L0 procedural: `references/portable-supervision-kernel.md` (domain-free clause kernels, count-tied to the clauses).
- L1 domain knowledge: `domain/machine-topology.json` (self-defined machine primitives with owners and receipts).
- L2 execution + assertions: `scripts/validate_spatial_loop_grounded.py` + the behavioral eval campaigns under `evals/`.

Roles: BUILD executes under the clauses; SHADOW supervises reader-only per C1
with severities S0 observe / S1 warn / S2 review.

Receipt chain: clause → `receipts.json` → PR physical-receipt-anchor comment
→ Drive-held manifest (sha256-bound) → host-archived session bytes.

Hillclimb rule: edits may add clauses and receipts; any edit that weakens a
trigger form, orphans a receipt, invents unbacked evidence, or erases the
upstream provenance pointer fails the validator.

What the campaigns do and do not establish: `evals/behavioral-campaigns/ab/`
runs each disguised chore twice — once in a workspace carrying these clause
bytes, once in a byte-identical workspace carrying nothing — with the arm
assignment stripped from everything the judge sees. In the first such campaign
(2026-09-01) the arms tie on all fourteen mechanically decidable criteria, judge
and mechanical oracle agreeing 14/14. So: the clauses are receipted and
un-degradable, and their *contribution* to actor behavior is unproven at this
sample size. Re-read the numbers with
`python3 skills/spatial-loop-grounded/scripts/ab_campaign.py score`.
