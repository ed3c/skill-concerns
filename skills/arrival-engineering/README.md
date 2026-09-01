# arrival-engineering

One question, mechanized: **for each declared capability, who consumes it,
through which bound exit, and at which measured arrival level - and does every
claim match?**

The class this bundle owns is *declared capability with no bound consumer, or a
consumption claim above its measured arrival*. Five instances of it surfaced in
a single day and every one was caught by hand. This is the owner.

Roles: **BUILD** appends topology rows and regenerates receipts under this
directory only, and lands through the repository's PR ceremony. **SHADOW** is
reader-only: it runs the island audit and reports at severities S0 observe /
S1 warn / S2 review, and never patches what it finds.

## Read route

1. [`AGENTS.md`](AGENTS.md) - the bundle contract.
2. [`README.md`](README.md) - this page.
3. [`SKILL.md`](SKILL.md) - clauses A1-A6, the DECLARED / EXERCISED /
   PRODUCTION arrival vocabulary this bundle owns, and the diagnostics the
   driver emits.
4. [`skill.json`](skill.json) - the concern split.
5. [`domain/capability-topology.json`](domain/capability-topology.json) - the
   audited rows and the receipt behind each recorded level.

## Run it

```sh
python3 scripts/audit_islands.py                    # SHADOW over this repository
python3 scripts/audit_islands.py --tree <clone> --topology <file>
python3 scripts/audit_islands.py --selftest
python3 scripts/validate_arrival_engineering.py --selftest
python3 scripts/gen_receipts.py                     # receipts.json's only author
```

The audit is read-only by measurement, not by promise: it digests the audited
tree before and after the pass and refuses its own report if the digest moved.

## Arrival levels, and the two axes they are not

- **DECLARED / EXERCISED / PRODUCTION** - this bundle's vocabulary, and it owns
  the definition. About *who reached the capability*.
- **L0 procedural / L1 domain / L2 execution** - the bundle-anatomy concern
  layers every admitted Skill uses. About *where bytes belong*.
- **L0_SOURCE_FREEZE .. L5_DELIVERY_AND_PRODUCTION** - the admission evidence
  ceiling in `registry.json`. About *what one commit proved*.

An earlier draft numbered arrival from L0 too, making three L-numberings on one
page, and shipped a validator clause requiring SKILL.md to keep them apart. The
arrival axis was the newest of the three and had no consumers, so it is the one
that moved: naming the levels removes the collision the prose was managing, and
the gate that read that prose was deleted with it.

## Where the findings go

Every provider ref in [`receipts.json`](receipts.json) is re-resolved by
`scripts/maintain_skills.py`, which already globs `skills/*/receipts.json` on a
cadence. That is how SHADOW rides an existing sweep instead of shipping a
scheduler.

## What this is not

Not runtime liveness (`dynamic-workflow`), not the code-intel method stack
(`control-code-intel`), not compiled context projections
(`context-closure-engineering`, whose closure laws clause A6 points at rather
than restates), and not supervised-execution conduct (`spatial-loop-grounded`).
