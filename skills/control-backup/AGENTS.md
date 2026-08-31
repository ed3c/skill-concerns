# AGENTS.md — control-backup

<!-- agent-next: none -->

This is the third and final Agent document for this Skill. Do not search for another `AGENTS.md`.

## Local read order

1. [`README.md`](README.md) — three-layer topology and receipt chain.
2. [`SKILL.md`](SKILL.md) — decision boundary and best-path entry.
3. [`domain/backup-topology.json`](domain/backup-topology.json) — L1 tiers/tools/volatile zones.
4. [`references/portable-backup-policy.md`](references/portable-backup-policy.md) — L0 kernel.
5. [`scripts/backup_driver.py`](scripts/backup_driver.py) — L2 execution + assertions.

## Stop laws

- A slow tier never reads live sources; it replicates the completed fast-tier snapshot.
- A copier that dies on one vanished file is not admitted for hot sources; churn is warning-class, real errors stay fatal.
- Rotation floors are computed from measured per-target snapshot cost; an unattainable threshold is a standing failure order.
- One writer per destination: PID-holding lock, dead-holder takeover, live holder never robbed.
- Secrets ride physically-held tiers only; model-mediated lanes carry text manifests only.
- No green light without: mount-point identity, key files at destination, exclusions effective, and an instrument proven able to go red.

## Completion

Run `python3 skills/control-backup/scripts/validate_control_backup.py`
and `python3 -m unittest discover -s skills/control-backup/tests`.
Report layer integrity, receipt bindings, and the L2 selftest outcome.
