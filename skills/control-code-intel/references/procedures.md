# Best-path procedures (L2 human-readable companion)

The canonical L2 is the executable driver + assertions
([`../scripts/code_intel_driver.py`](../scripts/code_intel_driver.py)); this file
is its human-readable companion. Each procedure ends in an ASSERTION the driver
encodes, not a "should work".

## Install the MCP servers

- Serena (dynamic, cross-repo, zero infra):
  `claude mcp add serena -s user -- serena start-mcp-server --context claude-code`
  and a `[mcp_servers.serena]` block in `~/.codex/config.toml` with
  `--context codex`.
- grepai (single repo, gob): `claude mcp add grepai -s user -- grepai mcp-serve <repo>`.
- ASSERT: a real query returns results; `Connected` alone is not usable.
- Note: a running session loads MCP at start; new tools require a restart.
- Both registrations were watched reaching `Connected` on the operator host once:
  receipts `grepai-mcp-connected` and `serena-mcp-connected`. Nothing here
  replays them, which is why each names its observer in `receipts.json`.

## Enable cross-repo (workspace, Postgres + pgvector)

1. Ensure Postgres is running; `createdb grepai`.
2. Build pgvector for the RUNNING Postgres major (a brew bottle may target a
   different major): `make PG_CONFIG=$(pg_config-for-that-major) && make install`,
   then `psql -d grepai -c 'CREATE EXTENSION vector'`.
3. `grepai workspace create <name>`; `grepai workspace add <name> <repo>` per repo.
4. `grepai mcp-serve --workspace <name>` for the MCP; `grepai watch --workspace <name>` to index.
5. ASSERT: `SELECT count(*) FROM chunks` is nonzero AND a repo-distinctive query
   returns the correct repo. Until both hold, cross-repo is not ready.

Step 2 is the one nothing here replays: the build against the running major and
the extension's own version string were watched once on the operator host
(receipt `pgvector-built-pg16`). Treat it as a host observation, not a
reproduction, and re-do it on any machine whose Postgres major differs.

## The backend-switch reindex gotcha

Switching a project from gob to Postgres leaves `.grepai/config.yaml`'s
`last_index_time` stamped. The new (empty) store then skips indexing as
"already indexed". Clear the stamp (`last_index_time: null`), restart the
watcher, and ASSERT nonzero chunks before searching.

## Keep the index to real source only

Exclude `.claude`, `.worktrees`, and remove stray nested `.grepai` roots inside
worktree copies (they register as phantom projects and serve duplicate paths).
ASSERT: search results cite the real repo path, not a worktree copy.

## Index freshness has an owner (verified 2026-08-31)

The index reflects local checkout bytes, not provider main; and a live index
needs a live watcher. Both failure modes were caught physically: a query for
a landed change missed because the local clone was days behind, and a
4.5-hour-old watcher sat frozen (static chunk count) with nothing noticing.

- Owner: a system service (launchd `com.neon.sync-code-intel`, every 15 min),
  not any agent session. It fast-forwards each workspace repo's main checkout
  (branch==main guard; git's own `merge --ff-only` machinery refuses when
  local state is in the way — no blunt dirty-check), then restarts the
  workspace watcher if `pgrep` finds none.
- ASSERT freshness end-to-end, not by proxy: after a land, a query distinctive
  to the landed change must return it. A running watcher pid is not freshness.
- Both failure modes and the cure were observed on the operator host in one
  session (receipt `freshness-needs-an-owner`); the service and its schedule
  live on that host, so nothing in this bundle replays them.

## The status tool is not workspace-aware (verified 2026-08-31)

`grepai_index_status` (and `grepai status`) reads the per-project context and
reports 0 files while the workspace store is populated and serving results.
Never judge workspace health from status: use a canary search with a known
answer, or `SELECT count(*) FROM chunks` on the workspace store. The
disagreement between the two readings was seen once, live, on the operator host
(receipt `status-not-workspace-aware`) and is not reproduced by anything here.

## Scoped vs cross-repo search

- One repo: `grepai search Q --workspace <name> --project <repo>`.
- All repos: `grepai search Q --workspace <name>` (results prefixed
  `<workspace>/<project>/`).
- Serena: `activate_project <repo>` then navigate; no per-repo setup.
