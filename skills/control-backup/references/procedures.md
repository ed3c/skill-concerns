# Best-path procedures (L2 human companion)

Concrete, gotcha-annotated procedures for the noodles operator machine.
Each gotcha is a receipt in [`../receipts.json`](../receipts.json); read the
affected procedure from source before acting - the map is maintained memory,
not permission to skip a physical readback.

## Run / verify the daily backup

The executable lives in its harness: `~/.noodles-ops/backup-noodles.sh`
(launchd `com.neon.noodles-backup`, 03:30 + StartOnMount + manual).

```
~/.noodles-ops/backup-noodles.sh --dry-run   # cheap verification surface
~/.noodles-ops/backup-noodles.sh             # real run (lock-guarded)
tail ~/.noodles-ops/backups/backup-noodles.log
```

- Green only counts after the script's own assertions: mount-point check,
  key files present at destination, exclusions effective.
- Gotcha `pipeline-exit-swallowed`: never verify with `cmd | head && echo OK`;
  the tail consumer returns 0 on a dead producer. Assert on file bytes.

## Copier requirements (hot sources)

- GNU rsync from brew is required (`/opt/homebrew/bin/rsync`); the wrapper
  maps exit 24 (vanished sources) to success and keeps everything else fatal.
- Gotcha `openrsync-hot-source-fatal`: the stock macOS rsync fails the whole
  run on one vanished file; it also ignores the `/./` relative anchor.
- Gotcha `hot-git-refs-vanish`: `.git` is part of the hot zone - do branch
  surgery and backups on the same tree with the tolerance in place.

## Changing exclusion filters

1. Edit the FILTERS array.
2. Sweep leftovers once: excluded paths already copied are PROTECTED from
   `--delete` at every destination (`exclude-protects-leftovers`); remove
   them by hand from the current local snapshot (USB converges via replicate).
3. `--dry-run`, then real run.

## Rotation on a constrained target (exFAT USB)

- Every snapshot costs full size (no hardlinks) plus ~1.6x cluster bloat on
  many small files; sockets cannot be copied there at all.
- Compute the floor before shipping it: disk minus foreign usage minus
  (keep-floor x measured snapshot cost) must fit both the min-free threshold
  and one new snapshot (`rotation-floor-unattainable-bug` is the shipped
  counterexample the driver replays).

## Cloud lane

- Drive MCP: text manifests only (`mcp-binary-infeasible`); assert the
  folder owner from returned metadata; account lock is path-embedded.
- Direct CloudStorage writes need the human to grant Full Disk Access to the
  hosting terminal app and restart it (`tcc-blocks-cloudstorage`); until
  then the tier logs SKIP with the exact grant instruction.
- No credentials on any cloud tier (`secrets-cloud-refused`); pem/token/auth
  material rides local + USB only.

## Restore

- USB alone restores a bare machine:
  `/Volumes/SANDISK/noodles-backup/latest/.noodles-ops/restore-from-sandisk.sh`
  (falls back to the local tier when USB is absent; optional arg picks a day).
- Cross-machine bootstrap: `~/.noodles-ops/restore-kit/bootstrap-new-machine.sh`
  with Brewfile + versions.txt (also on Drive `noodles-restore-kit/`).
- Rebuild, never restore: serena/grepai/SCIP indexes, codex-isolation,
  materialized providers.
