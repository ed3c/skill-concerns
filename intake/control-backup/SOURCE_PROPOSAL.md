# SOURCE PROPOSAL — control-backup

Owner design brief. Source: the 2026-08-30/31 production backup build-out
sessions on the noodles operator machine, in which a three-tier live-system
backup (local APFS hardlink snapshots → exFAT USB rotation → cloud
text-manifest lane) was designed, broken eight distinct ways by reality, and
repaired to a verified green state. Every claim admitted into the Skill
carries a physical receipt from those sessions; nothing speculative is
admitted.

## What was physically established

1. A live agent-runtime home directory is hot everywhere — per-run session
   dirs, materialized providers, per-lane git worktrees, `.git` refs during
   branch surgery, and the assistant's own config file all mutated during
   copy windows and each killed a strict copier run.
2. macOS openrsync fails the whole transfer on one vanished/changed file;
   GNU rsync 3.5 degrades the same events to warning-class exit 24. This is
   the difference between a backup that converges and one that whack-a-moles.
3. Freeze-then-replicate: slow tiers (USB) must copy from the completed
   fast-tier snapshot; copying live sources over a long window failed twice,
   the frozen-source copy succeeded on the first try.
4. `--link-dest` hardlink dedup was inode-verified; the same-second/same-size
   quick-check false negative was reproduced (an instrument must be shown to
   go red before its green counts).
5. exFAT: no hardlinks (every snapshot costs full size), no unix sockets
   (`mkstempsock: Operation not supported`), ~1.6x cluster bloat on a
   many-small-files tree. Rotation floors must be computed per target from
   measured snapshot cost — an unattainable min-free threshold guarantees
   permanent failure (shipped, caught at review, fixed).
6. Two backup writers raced one destination (calendar trigger + manual run);
   a mkdir lock with PID liveness takeover ended the class. kill -9 bypasses
   traps, so orphan locks must be adopted, not obeyed.
7. rsync excludes protect stale destination copies from `--delete`; filter
   changes require a one-time leftover sweep (111M + 383M of protected
   leftovers were removed by hand).
8. TCC denies terminal processes access to `~/Library/CloudStorage`;
   `tmutil localsnapshot` works unprivileged but `mount_apfs -s` needs root —
   both cloud-folder writes and APFS-snapshot reads are out for unattended
   agents until a human grants what only a human can grant.
9. A model-mediated upload lane (MCP) carries file content through model
   context: text manifests are fine, a 5 MB binary is not. Secrets ride only
   physically-held tiers.
10. The restore entrypoint must travel inside the backup medium; derived
    artifacts (search indexes, caches, isolation venvs) are rebuilt on
    restore, never backed up.
