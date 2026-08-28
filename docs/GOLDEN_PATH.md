# Golden Path

## 1. Select a source

An Agent or human may identify a source Skill, owner design brief, failure transcript, or repository capability that should become a reusable Skill.

Selection is probabilistic and creates no admission state.

## 2. Freeze the source

Before refactoring:

- bind repository URL and exact 40-character commit when the source is Git;
- bind the exact source path;
- hash every selected source file;
- or materialize an owner design brief and hash that file;
- record method references separately from candidate evidence.

A branch name, issue title, chat summary, or URL without bytes is not a source lock.

## 3. Extract concerns

Classify each load-bearing rule as:

```text
universal invariant
portable convention
domain contract
execution mechanism
incidental fact
```

Keep universal invariants and portable conventions in the generic Skill. Put domain contracts in declared adapter/domain paths. Put mechanics in scripts/tests. Leave incidental facts discoverable.

## 4. Refactor the candidate

Build the smallest bundle that preserves the source's load-bearing strengths. Do not copy an upstream repository's live state, credentials, provider bindings, worktree topology, or historical receipts.

## 5. Bind routes and falsifiers

Every declared executable route must reach its checker, test, and suite runner. Add a negative control that breaks the route and turns the suite red.

Every semantic rule that can fail silently needs a planted mutation, such as:

- reachable terminal without oracle;
- `VERIFIED` with static-only evidence;
- skipped path without blocker;
- changed feature without journey;
- fourth Agent document;
- stale admission hash.

## 6. Execute hermetic evaluation

Run the candidate and all controls under one exact tree. Failed controls remain in the case inventory; they are expected failures, not deleted noise.

## 7. Bind the admission receipt

The receipt covers:

- the complete Skill tree;
- selected shared contracts;
- source-lock identity;
- executed control names and states;
- highest reached evidence layer;
- every higher unexercised layer.

The receipt cannot include itself in its digest and cannot replace execution.

## 8. Publish exact-head verification

The pull-request head runs the read-only workflow. A later commit invalidates the earlier check. Promotion is eligible only for the exact checked head.

## 9. Consume through an adapter

A downstream repository chooses the admitted Skill and supplies its own domain adapter/runtime. Consumer success requires separate evidence and does not retroactively change this repository's admission receipt.
