# control-code-intel

Domain-rich skill controlling the physically-verified code-intelligence stack
(grepai, Serena, tree-sitter, SCIP, SQLite) across one or many repositories.

Three layers, one method (repo ARCHITECTURE L0/L1/L2):
- L0 semantic kernel: `references/portable-code-intel-policy.md` (portable, domain-independent tool-selection and proof semantics).
- L1 domain knowledge: `domain/code-intel-topology.json` (capabilities, states, backends, selectors, environment constraints).
- L2 execution + assertions: `scripts/code_intel_driver.py` (act/poll/observe/assert/persist), with `references/procedures.md` as its human companion.

Every admitted capability carries a physical receipt (`receipts.json`) from the
2026-08-31 wiring + cross-repo session; the L2 driver replays their assertions.
LanceDB is explicitly not admitted (measured drop). Hillclimb gate: the
validator fails closed on a weakened layer, an unbacked tool, or a defused
negative control.
