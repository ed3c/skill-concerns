# Portable backup policy (L0 procedural)

Domain-independent decision policy for backing up a live, mutating tree.
No product names, no machine paths: these rules survive a change of
runtime, filesystem vendor, or scheduler.

## 1. The race law

A backup of a live system is a copy racing a writer. Every design decision
is a decision about that race: shrink the window, freeze the source, or
tolerate the churn. A design that does none of the three will fail on a
schedule set by the writer, not by you.

## 2. Freeze-then-replicate

Only the fastest tier may read live sources, because its window is smallest.
Every slower tier (removable media, network, cloud) replicates from the
completed fast-tier snapshot. A frozen source makes the slow tier's window
irrelevant: the copy can take an hour and stay consistent.

## 3. Copier tolerance

On a hot source, files vanish and change between the copier's file-list and
its copy. A copier that fails the entire run on one such event cannot back
up a live system; require one that degrades these to warning-class results,
and map that warning class to success explicitly in the calling code — not
by ignoring all failures.

## 4. Volatile-subtree isolation

Runtime-managed churn zones (per-run scratch, materialized caches, lane
workspaces) are excluded wholesale from the wide copy. Their durable subset
travels in a dedicated seconds-scale copy with bounded retries: the shorter
window multiplied by retries drives collision probability toward zero.
Excluding churn paths one at a time as they bite does not converge — new
ones appear at the writer's pace. Version-control internals are part of the
hot zone: refs vanish during branch surgery like any other file.

## 5. Rotation math must be attainable

For each target: measure the snapshot cost on that filesystem (dedup
features differ; allocation overhead differs), then derive the keep floor
and minimum-free threshold from device capacity minus foreign usage. A
threshold above the attainable maximum is a standing order to fail every
day. Prune before copy, never after. History depth belongs on the tier
whose filesystem makes history cheap; a tier without dedup rotates few full
copies and that is a fact to encode, not to regret.

## 6. Single writer

Recurring jobs acquire triggers over time (schedule, device attach, manual
run) and triggers race. One lock, holding the owner's process id; a lock
whose owner is dead is adopted, because forced kills bypass cleanup
handlers. Without liveness takeover, the first crash converts every future
run into a silent skip.

## 7. Assert before declaring success

- The destination must be proven to be the intended medium (a mount-point
  check), or an absent volume silently collects the backup on the boot disk.
- Key files must be asserted present at the destination after the copy; the
  exclusions must be asserted effective (the excluded path absent).
- The instrument itself must be shown able to go red: a success printed
  after a pipeline whose tail consumer swallows exit codes, or a
  change-detector defeated by same-second writes, is a green lamp wired to
  the ceiling light. Plant a defect once and watch it fail before believing
  any pass.

## 8. Exclusion changes need a leftover sweep

A copier's exclusion also protects already-copied content at the
destination from deletion. Adding an exclusion after content has landed
strands stale bytes there until swept once by hand. Treat every filter
change as a migration with a cleanup step.

## 9. Secret tiering

Credentials ride only tiers whose medium the owner physically holds. Cloud
tiers carry configuration and manifests, never key material. A lane that
moves bytes through a model's context window is a text-manifest lane: small
declarative files only, both for size physics and for exposure discipline.

## 10. Restore is part of backup

The restore entrypoint travels inside the backup medium, so a bare machine
plus the medium suffices. Derived artifacts — search indexes, caches,
isolation environments — are rebuilt from their inputs on restore, never
backed up; record the rebuild command where the restore script lives.
