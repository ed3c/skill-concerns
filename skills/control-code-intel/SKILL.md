---
name: control-code-intel
description: >
  Control and use the physically-verified code-intelligence stack -
  grepai retrieval, Serena symbol navigation/edit, tree-sitter structural
  readback, SCIP validation, SQLite evidence - across one or many
  repositories. Use when a task needs semantic retrieval, symbol navigation,
  structural byte-range proof, or cross-repository code search, and the
  answer must be reproducible from evidence, not trusted from a model's
  guess.
---

# Control Code-Intel

The code-intel stack has two access layers; a task uses exactly the layer its
question needs, never both by reflex.

- **Interactive (MCP)**: Serena and grepai exposed as MCP tools for agents.
- **Internal probes (CLI)**: the noodles-landed adapters that run the tools as
  subprocesses and emit digest-bound evidence receipts.

Admitted tools are exactly those code-intelligence v1 converged on
([`domain/code-intel-topology.json`](domain/code-intel-topology.json)):
grepai, Serena, tree-sitter, SCIP, SQLite. **LanceDB is not admitted** - it
was measured against grepai on the same 17-task corpus and dropped on a
zero-retrieval-gain result (receipt `lancedb-dropped`), not on taste.

## Decision boundary

For each task, pick the tool by the shape of the question, per
[`references/portable-code-intel-policy.md`](references/portable-code-intel-policy.md):

1. "where is the code that does X" by intent, fuzzy -> **grepai** semantic retrieval.
2. "find this symbol / its callers / its definition" exactly -> **Serena** navigation.
3. "change exactly this symbol body, nothing else" -> **Serena** bounded edit.
4. "what are the exact byte ranges of this definition, provably" -> **tree-sitter** structural readback, cross-checked against the language AST.
5. "does this index reproduce at an exact commit" -> **SCIP** validation.
6. "record/re-verify that this evidence still holds against current bytes" -> **SQLite** exact-subject ledger.
7. "search across more than one repository" -> the grepai **workspace** (Postgres+pgvector backend), never per-repo gob.

Never assert a retrieval result as truth. Every code-intel answer is either
re-verifiable against current source bytes (the ledger/structural path) or is
a ranked candidate the caller must confirm (the retrieval path). State which.

## Backends and their boundary

- **gob (per-repo)**: single-repository, file-backed, zero infra. Correct for one repo.
- **Postgres + pgvector (workspace)**: multi-repository. Required for cross-repo. Needs the `vector` extension matching the running Postgres major version.

A workspace whose Postgres lacks a version-matched `pgvector` fails closed at
store init - it does not silently fall back. Do not claim cross-repo readiness
until a real cross-repo search returns the correct repository for a
repo-distinctive query (receipt `cross-repo-verified`).

## Best-path procedures

The concrete, gotcha-annotated procedures live in
[`references/procedures.md`](references/procedures.md): install the MCP servers,
build pgvector for the running Postgres major, create and populate a workspace,
force a full reindex after a backend switch, run scoped and cross-repo searches.
Read the affected procedure from source; the map is maintained memory, not
permission to skip a physical readback.

## Hard constraints

- Do not report an MCP as usable on "connected" alone: connected is the wire, a
  returned result is the property. Prove with one real query before claiming use.
- Do not index worktree copies or nested checkouts: exclude `.claude`,
  `.worktrees`, and stray nested `.grepai` roots, or the index serves duplicate
  paths instead of the real source.
- A backend switch leaves the project's `last_index_time` stamped; the new
  backend then skips as "already indexed" while its store is empty. Clear the
  stamp to force a full reindex, and verify the store's chunk count is nonzero.
- Cross-repo activation is provider-owned infra (Postgres, pgvector, ollama);
  custody stays at the version-and-DSN readback level, like any provider.

## Knowledge placement

These are the skill-concern layers (L0 procedural / L1 domain knowledge /
L2 execution + assertions): they answer where a piece of knowledge lives.
They are a different axis from the Compilation stages C0/C1/C2
(C0 semantic kernel / C1 self-contained contract / C2 best-path procedure),
which answer how evidence compiles into the rendered product, and from
Shadow severity S0/S1/S2 (S0 observe / S1 warn / S2 review). The three
namespaces must never be mixed; a C stage is written with the word
Compilation on first use so a zero-context reader can build the namespace.

- L0 procedural — portable, domain-independent tool-selection and proof
  semantics: [`references/portable-code-intel-policy.md`](references/portable-code-intel-policy.md).
- L1 domain knowledge — stack topology, tools, states, backends:
  [`domain/code-intel-topology.json`](domain/code-intel-topology.json).
- L2 execution + assertions — drivers, procedures, gotchas:
  [`references/procedures.md`](references/procedures.md) and [`scripts/code_intel_driver.py`](scripts/code_intel_driver.py).
- Physical receipts for every admitted capability: [`receipts.json`](receipts.json).
