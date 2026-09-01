# red-team

One question, mechanized: **does this artifact carry a pattern class we have
already paid for, and does the class's own experiment confirm it here?**

The class this bundle owns is *a judgement method with no pinned bytes*. The
adversarial method behind the strongest findings of the last five waves -
rewrite-all-to-the-exit experiments, planted-direction replay, producer re-runs
in throwaway clones, pristine-main controls, the GraphQL second-arrival probe -
lived in dispatcher prompt text and scratchpad notes. This is its owner.

Roles: **BUILD** folds one adjudicated class into the catalogue and regenerates
receipts under this directory only, landing through the repository's PR
ceremony. **SHADOW** is reader-only: it matches a boundary's artifacts against
the catalogue, runs the matched classes' experiments, and reports at severities
S0 observe / S1 warn / S2 review, never patching what it finds.

## Read route

1. [`AGENTS.md`](AGENTS.md) - the bundle contract.
2. [`README.md`](README.md) - this page.
3. [`SKILL.md`](SKILL.md) - clauses R1-R7, the catalogue contract, the diagnostics.
4. [`skill.json`](skill.json) - the concern split.
5. [`domain/catalogue.json`](domain/catalogue.json) - the pinned classes, their provenance, recipes and lifecycle.

## Run it

```sh
python3 scripts/shadow_driver.py --bundle <dir> --wave <name> --boundary <name>
python3 scripts/shadow_driver.py --bundle <dir> --append-record
python3 scripts/shadow_driver.py --add-class <class.json>
python3 scripts/validate_red_team.py --selftest
python3 scripts/gen_receipts.py
```

A bundle is one boundary's artifacts in four directories - `diffs/`,
`reports/`, `receipts/`, `issues/`. The pass is read-only by measurement, not
by promise: it digests the bundle before and after and refuses its own report
if the digest moved.

## Where the findings go

Nowhere, by design. The monitor manufactures admission-grade evidence and the
dispatcher files with it: `render_demonstration()` emits a block that drops
verbatim into an issue body's observer-demonstration section and survives that
gate's fence-stripping, proven by the round-trip fixture rather than asserted.
The only real-time channel out is one escalation signal to the dispatcher, for
two enumerated urgent classes, carrying no instruction and no patch.

## The declining curve

Every run appends one record to [`domain/run-ledger.json`](domain/run-ledger.json):
classes sampled, hits per class, novel-class candidates, judge gaps, duplicate
blocks. Known-class recurrence must trend to zero as classes gate. Three
post-admission waves without a falling curve is a finding delivered to the
dispatcher - the instrument reports its own failure to bend the curve rather
than presuming success.

## What this is not

Not supervised-conduct clause judgment (`spatial-loop-grounded`), not context
projection (`context-closure-engineering`), not runtime liveness
(`dynamic-workflow`), and not the architecture angle the unadmitted
`shadow-architect` will carry (ed3c/skill-concerns#75). Those read and
question; this one executes falsification. The differential is the verb.
