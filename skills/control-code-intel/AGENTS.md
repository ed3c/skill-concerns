# AGENTS.md — control-code-intel

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — three-layer topology and receipt chain.
2. [`SKILL.md`](SKILL.md) — decision boundary and best-path entry.
3. [`domain/code-intel-topology.json`](domain/code-intel-topology.json) — L1 capabilities/states/backends.
4. [`references/portable-code-intel-policy.md`](references/portable-code-intel-policy.md) — L0 kernel.
5. [`scripts/code_intel_driver.py`](scripts/code_intel_driver.py) — L2 execution + assertions.

## Stop laws

- Connected is not usable: prove one real query before claiming a capability.
- Retrieval is a candidate, never truth; prefer re-verifiable structural/ledger paths for load-bearing answers.
- Cross-repo needs a version-matched pgvector; store init fails closed otherwise.
- A tool enters the admitted set only on measured advantage with a confound-isolating control; an honest negative drops it (LanceDB).
- A backend switch orphans last_index_time; clear it and assert nonzero chunks.

## Completion

Run `python3 skills/control-code-intel/scripts/validate_control_code_intel.py`
and `python3 -m unittest discover -s skills/control-code-intel/tests`.
Report layer integrity, receipt bindings, and the L2 selftest outcome.
