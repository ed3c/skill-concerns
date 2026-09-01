# AGENTS.md — dynamic-workflow

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — three-layer topology, procedure mapping, deferred layers.
2. [`SKILL.md`](SKILL.md) — the one law and the four lane classes.
3. [`domain/dispatch-runtime-topology.json`](domain/dispatch-runtime-topology.json) — L1 observables for both runtimes.
4. [`references/portable-supervision-policy.md`](references/portable-supervision-policy.md) — L0 kernel instantiation.
5. [`scripts/liveness_driver.py`](scripts/liveness_driver.py) — L2 execution + assertions.

## Stop laws

- The completion notification is the only death certificate. Age never produces `dead`; only a death signature does.
- A stamped rollup field (`alive`, `status`, `health`) is not an observation. Derive liveness from ledger timestamps, never from a stamp, a process table, or a file mtime.
- The reader never writes to the observed system, never gates a landing, never repairs a lane.
- Ceremony correctness belongs to `control-noodle`. Point at it; a restated copy is drift.
- A lens-drift finding is FILED, never applied inline. The only automation permitted is scheduling a maintenance pass that still lands through the full change ceremony.

## Completion

Run `python3 skills/dynamic-workflow/scripts/validate_dynamic_workflow.py`
and `python3 -m unittest discover -s skills/dynamic-workflow/tests`.
Report layer integrity, pointer discipline, receipt bindings, and the L2 selftest outcome.
