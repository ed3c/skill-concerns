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

## Enable cross-repo (workspace, Postgres + pgvector)

1. Ensure Postgres is running; `createdb grepai`.
2. Build pgvector for the RUNNING Postgres major (a brew bottle may target a
   different major): `make PG_CONFIG=$(pg_config-for-that-major) && make install`,
   then `psql -d grepai -c 'CREATE EXTENSION vector'`.
3. `grepai workspace create <name>`; `grepai workspace add <name> <repo>` per repo.
4. `grepai mcp-serve --workspace <name>` for the MCP; `grepai watch --workspace <name>` to index.
5. ASSERT: `SELECT count(*) FROM chunks` is nonzero AND a repo-distinctive query
   returns the correct repo. Until both hold, cross-repo is not ready.

## The backend-switch reindex gotcha

Switching a project from gob to Postgres leaves `.grepai/config.yaml`'s
`last_index_time` stamped. The new (empty) store then skips indexing as
"already indexed". Clear the stamp (`last_index_time: null`), restart the
watcher, and ASSERT nonzero chunks before searching.

## Keep the index to real source only

Exclude `.claude`, `.worktrees`, and remove stray nested `.grepai` roots inside
worktree copies (they register as phantom projects and serve duplicate paths).
ASSERT: search results cite the real repo path, not a worktree copy.

## Scoped vs cross-repo search

- One repo: `grepai search Q --workspace <name> --project <repo>`.
- All repos: `grepai search Q --workspace <name>` (results prefixed
  `<workspace>/<project>/`).
- Serena: `activate_project <repo>` then navigate; no per-repo setup.
