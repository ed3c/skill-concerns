# dynamic-workflow

Reader-only supervision of dispatch runtimes: Claude Code Workflow waves and
codex daemon sessions. Kind `domain-rich`, evidence ceiling `L3_HERMETIC`.

Authored under the pinned `create-verification-skill` procedure
(`policy/upstream-pins.json`), read-only adaptation:

| Procedure section | Here |
|---|---|
| Launch | N/A by construction — a reader starts nothing |
| Doctor | `scripts/liveness_driver.py --selftest` |
| Drive | `scripts/liveness_driver.py --observe <run-record-path>` |
| Evidence | `$DYNAMIC_WORKFLOW_EVIDENCE` (default `$TMPDIR/dynamic-workflow/`), printed by the driver |
| Cleanup | N/A by construction — no instance is created, and evidence is never removed |

## Three layers

| Layer | Path | Holds |
|---|---|---|
| L0 procedural | `references/portable-supervision-policy.md` | delivery discipline, S0/S1/S2, actor-unaware judging, judge rules v3, the maintain coupling |
| L1 domain | `domain/dispatch-runtime-topology.json` | both runtimes' observables and the classification law as data |
| L2 execution | `scripts/liveness_driver.py`, `references/prompts/*.md` | the driver, its assertions, and the prompt files the dispatcher references by path |

## Receipt chain

`receipts.json` → the real archives it was read from → `admissions/dynamic-workflow.json`
(content-bound) → the hosted exact-head check.

## Not claimed at admission

- **L4_MATCHED_LIVE_RUNTIME / L5_DELIVERY_AND_PRODUCTION** — not exercised.
- **Dispatcher-side single-source proof** — a wave script that references
  `references/prompts/monitor-prompt.md` and `references/prompts/judge-prompt.md`
  by path, with its judge citing those bytes, lives in the dispatcher's harness
  outside this repository. DEFERRED, filed *for the dispatcher's ledger append*.
- **Terminal-stamp question** — 79 of 600 real codex sessions carry a terminal
  `exited` stamp but no completion notification and no failure stamp, so they
  stay at `stalled-suspect` indefinitely. Whether a notification exists that this
  reader is not yet reading is DEFERRED, filed at
  `skills/dynamic-workflow/domain/dispatch-runtime-topology.json`
  (`runtimes.codex-noodle-session.observed.classified_by_this_skills_driver`),
  owner `dynamic-workflow`. The law is not widened to close it.

## Completion

```bash
python3 skills/dynamic-workflow/scripts/validate_dynamic_workflow.py
python3 -m unittest discover -s skills/dynamic-workflow/tests
```
