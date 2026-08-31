# control-backup

Domain-rich skill controlling the physically-verified backup decision
boundary for live systems: freeze-then-replicate tiering, hot-source copier
tolerance, per-target rotation math, single-writer locking, secret tiering,
and assert-before-success verification.

Three skill-concern layers, one method (distinct from the Compilation
stages C0/C1/C2 and from Shadow severity S0/S1/S2 — the three namespaces
must never be mixed):
- L0 procedural: `references/portable-backup-policy.md` (portable, domain-independent race/rotation/lock/assertion policy).
- L1 domain knowledge: `domain/backup-topology.json` (tiers, tools, volatile zones, secrets set, restore entrypoints).
- L2 execution + assertions: `scripts/backup_driver.py` (act/observe/assert with real-rsync hazard reproductions), with `references/procedures.md` as its human companion.

Every admitted claim carries a physical receipt (`receipts.json`) from the
2026-08-30/31 backup build-out sessions; the L2 driver replays their
assertions, including two live hazard reproductions (same-second quick-check
defeat, exclusion-protected leftovers) against the host's real rsync.
openrsync is explicitly not admitted for hot sources (three observed fatal
runs). Hillclimb gate: the validator fails closed on a weakened layer, an
unbacked tool, or a defused negative control.
