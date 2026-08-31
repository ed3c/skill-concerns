# Portable code-intel policy (L0 procedural)

Domain-decoupled decision rules for using a code-intelligence stack. These
hold for any grepai/Serena/tree-sitter/SCIP/SQLite-shaped stack; the concrete
tool names, pins, and paths belong to the L1 domain-knowledge layer, not to
this procedural layer.

## Tool selection by question shape

The failure mode is reaching for the nearest tool instead of the one the
question's shape demands. Match shape to tool:

- **Fuzzy intent, "where does X happen"** → semantic retrieval. Output is a
  ranked candidate list. It answers "probably here", never "here".
- **Exact symbol identity, "this function / its callers / its definition"** →
  symbol navigation (LSP). Output is exact locations. It answers "here".
- **Bounded mutation, "change exactly this symbol"** → symbol-scoped edit, not
  a text replace. The edit is confined to one semantic node.
- **Provable extent, "the exact byte range of this definition"** → structural
  readback, cross-checked against the language's own parser. The cross-check is
  what makes the range provable rather than asserted.
- **Reproducibility, "does this index hold at an exact commit"** → commit-pinned
  index validation.
- **Persistence, "is this evidence still true"** → an exact-subject ledger that
  re-verifies against current source bytes on read.
- **More than one repository** → a multi-repo store, never a fan-out of
  single-repo indices.

## Evidence discipline

- **Retrieval is a candidate, never truth.** A semantic hit is a hypothesis the
  caller confirms by reading the cited bytes. Reporting a retrieval score as an
  answer is the representation-vs-property error: the score is the
  representation, the confirmed code is the property.
- **Structural and ledger paths are re-verifiable.** Their claims bind to
  current source bytes and fail closed when the bytes moved. Prefer them when
  the answer is load-bearing.
- **Connected is not usable.** A tool that connects but returns nothing is not
  in use. Prove one real query before claiming a capability.

## The drop-on-measured-loss rule

A candidate tool enters the admitted set only on measured advantage over the
incumbent on the same task corpus, with a control that isolates the tool's own
contribution from confounds (e.g. a store-less arm that fixes chunks, vectors,
and metric so only the store varies). An honest negative - the candidate loses
or ties - is a valid, receipt-bearing outcome and the correct disposition is to
drop it. Adding a tool that relieves no failure mode and adds only latency and
footprint is negative work, however fashionable the tool.

## Cross-repo as infra, not magic

Multi-repo search is a provider-owned backend (a database, a vector extension,
an embedder), not a feature that appears by configuration alone. Its readiness
is proven by a repo-distinctive query returning the correct repository, not by
a green "connected" status. Custody of the backend stays at the
version-and-connection readback level, like any pinned provider.
