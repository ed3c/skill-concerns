---
name: control-backup
description: >
  Control the physically-verified backup decision boundary for live systems -
  tier architecture (freeze-then-replicate), copier tolerance on hot sources,
  per-target rotation math, single-writer locking, secret tiering, and
  assert-before-success verification. Use when designing, operating, or
  reviewing a recurring backup of a mutating tree (an agent runtime, a home
  directory, a service state dir) where "the copy ran" must be upgraded to
  "the copy is provably restorable", and every green light must be backed by
  evidence, not by exit-code folklore.
---

# Control Backup

A backup of a live system is a copy racing a writer. This Skill owns the
decision boundary for that race: which tier reads live bytes, which copier
survives churn, when a green light may be believed.

## Decision boundary

For each task, pick the path by the shape of the question, per
[`references/portable-backup-policy.md`](references/portable-backup-policy.md):

1. "copy a mutating tree" -> **freeze-then-replicate**: only the fast first
   tier reads live sources; every slower tier replicates from the completed
   fast-tier snapshot (receipt `freeze-then-replicate-verified`).
2. "the copier keeps dying on files that vanish mid-read" -> a
   **vanish-tolerant copier** (warning-class exit for churn) plus
   **volatile-subtree isolation**: exclude runtime churn zones wholesale,
   carry their durable subset in a dedicated seconds-scale copy with bounded
   retries. Per-directory whack-a-mole does not converge (receipts
   `openrsync-hot-source-fatal`, `gnu-rsync-exit24`, `volatile-subtree-isolated`).
3. "how many snapshots fit / the disk is filling" -> **per-target rotation
   math** from measured snapshot cost on that filesystem; a min-free
   threshold above the attainable maximum guarantees permanent failure.
   Prune before copy (receipts `exfat-no-hardlink`, `rotation-floor-unattainable-bug`).
4. "several triggers can start the job" -> **single-writer lock** with owner
   PID and dead-holder takeover; concurrent writers on one destination are a
   proven live failure, and kill -9 leaves orphan locks (receipt `single-writer-race`).
5. "can secrets ride this tier" -> secrets ride only physically-held tiers;
   a cloud lane carries no credentials; a model-mediated lane is
   text-manifest-only because content transits model context (receipts
   `secrets-cloud-refused`, `mcp-binary-infeasible`).
6. "is the backup good" -> **assert before declaring success**: destination
   is a real mount point, key files exist at the destination, exclusions
   held, and the measuring instrument itself has been shown able to go red
   (receipts `mount-point-guard`, `same-second-quickcheck-hazard`,
   `pipeline-exit-swallowed`).
7. "restore" -> the restore entrypoint travels inside the backup medium;
   derived artifacts (indexes, caches, isolation envs) are rebuilt, never
   copied (receipt `restore-entrypoint-on-medium`).

## Hard constraints

- Never point a slow tier at live sources; the copy window is the failure
  window, and a hot `.git` is still hot (receipt `hot-git-refs-vanish`).
- Never accept a copier that fails the whole run on one vanished file for a
  hot source; on this platform that is the stock openrsync (not admitted).
- Never change exclusion filters without a leftover sweep: excludes protect
  stale destination copies from `--delete` (receipt `exclude-protects-leftovers`).
- Never trust an assertion instrument that has not been shown to go red: a
  trailing pipeline consumer eats exit codes, and a same-second write defeats
  the mtime quick-check silently.
- Never write to a removable-volume path without proving it is a mount point;
  an absent volume leaves a same-named directory on the boot disk.
- Unattended agents do not get APFS snapshot mounts (root) or CloudStorage
  writes (TCC); design around the grant a human has not yet made, and say so.

## Knowledge placement

These are the skill-concern layers (L0 procedural / L1 domain knowledge /
L2 execution + assertions): they answer where a piece of knowledge lives.
They are a different axis from the Compilation stages C0/C1/C2 and from
Shadow severity S0/S1/S2; the three namespaces must never be mixed.

- L0 procedural — portable, domain-independent backup decision policy:
  [`references/portable-backup-policy.md`](references/portable-backup-policy.md).
- L1 domain knowledge — tier topology, tools, volatile zones, secrets set:
  [`domain/backup-topology.json`](domain/backup-topology.json).
- L2 execution + assertions — drivers, procedures, gotchas:
  [`references/procedures.md`](references/procedures.md) and
  [`scripts/backup_driver.py`](scripts/backup_driver.py).
- Physical receipts for every admitted claim: [`receipts.json`](receipts.json).
