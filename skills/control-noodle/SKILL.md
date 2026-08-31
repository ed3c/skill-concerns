---
name: control-noodle
description: >
  Control and verify the source-frozen Noodles Issue-to-reconcile lifecycle
  through explicit Feature and Code Maps. Use when a Noodles change must be
  mapped to required journeys, operated through supported control surfaces,
  watched read-only while a fleet runs, or reported with exact proof and
  blockers.
---

# Control Noodle

Use this Skill for the bounded supervised lifecycle declared in [`domain/feature-map.json`](domain/feature-map.json). Do not treat it as authority to start, mutate, merge, or reconcile a live runtime unless the current task separately authorizes those actions and the target-local preconditions are physically present.

## Decision boundary

For each task:

1. bind the exact repository revision and actor-visible intent;
2. confirm `domain/composition.json` matches the admitted procedure and frozen domain subjects;
3. locate affected Code Map nodes from direct source readback;
4. compile those nodes through `domain/feature-code-map.json` into affected Feature Map transitions and required journeys;
5. reject unknown or unmapped code nodes instead of guessing ownership;
6. establish runtime, session, worktree, provider, and cleanup preconditions;
7. execute only supported domain-adapter operations;
8. collect observable evidence for the same exact subject;
9. reconcile the complete required-journey denominator;
10. report `VERIFIED`, `PARTIALLY_VERIFIED`, `BLOCKED`, or `NOT_VERIFIED` without evidence promotion.

## Knowledge placement

- Portable decision rules: [`references/portable-control-policy.md`](references/portable-control-policy.md).
- Domain control surface and constraints: [`references/control-surface.md`](references/control-surface.md).
- Behavioral topology: [`domain/feature-map.json`](domain/feature-map.json).
- Implementation topology: [`domain/code-map.json`](domain/code-map.json).
- Cross-graph ownership: [`domain/feature-code-map.json`](domain/feature-code-map.json).
- Concrete bindings: [`domain/domain-adapter.json`](domain/domain-adapter.json).

Read only the affected domain artifacts. The map is maintained memory, not permission to skip current source or runtime readback.

## Failure-edge routing

Trigger-form entries for the operational edges this lifecycle actually produced under supervision. Each row is signal → check → action. Every semantic named here is owned by the target repository's own gate or receipt; these rows route to that owner and never restate it.

| Signal | Check | Action |
|---|---|---|
| the provider rejects branch creation for an already-admitted subject | join the remote execute-claim branch against its subject Issue state: closed Issue = residue, open with no live session = dead claim, open with a pull request = in-flight | read the rejection as a foreign claim, not a cycle failure, and record it as a skip carrying its blocker; atomic claim ownership sits with `ed3c/noodles#138` |
| empty schedule proposals repeat while the backlog adapter still reports schedulable subjects | list every remote execute-claim branch, triage each row as above, then compare the claimed components against the frontier receipt | escalate with the frontier receipt quoted verbatim; never substitute a re-derived causal story, and never touch the scheduler first — one stale claim starves a whole repository under repo-scoped exclusion; frontier semantics are owned by `ed3c/noodles#190` and `#191` |
| one active order defers every sibling for a full idle generation | ask whether that order's session is still alive before reading the deferral as correct exclusion | expire the dead claim at its owning surface |
| the run that gates landing predates the `awaiting_land` flip and nothing re-triggers it | select the run by name and compare its head against the branch tip; a cancelled run is a superseded head, not a failure | re-trigger against the current tip; handoff ordering is owned by `ed3c/noodles#137` |
| execution exits after commit but before handoff | ask whether the exact head was handed to the provider lane at all | leave the branch unmerged; an unverified branch never lands locally |

## Monitor mode

Monitor mode is the second consumption of these same Skill bytes: a reader watches a running fleet and steers it, judging conformance against this document read-only. Operator mode acts; monitor mode reads. There is deliberately no second rubric — a steer quoting the playbook both parties hold carries authority, while a steer from a separate supervisory document starts a standards dispute and re-creates acceptance-parameter drift at the Skill layer. Independence for *correctness* is already owned by the stronger layer (trusted verify) and is not duplicated here.

### Consumption contract

- The monitor reads the same pinned Skill bytes the executor consumes, read-only.
- Where compiled route bundles exist (`ed3c/noodles#174`), the monitor consumes the same digest-bound bundle the executor received, as evaluation data only.
- Consumption is event-driven on session and loop event records. No polling loops. Context cost is bounded by the shared bundle; watching N executors on distinct routes costs N bundle contexts.

### Trigger table

| Signal | Check | Steer or escalate |
|---|---|---|
| session record silent past the wedge threshold | last event timestamp against the threshold | escalate — silence cannot wait for a stage boundary |
| tests flip red mid-execution | failing output against the last passing head | steer at the next stage boundary, quoting the failing output |
| writes land outside the atom's declared surface | changed paths against the atom's declared subject | steer at the next stage boundary; a runaway write pattern escalates instead |
| empty-proposal streak while the backlog reports schedulable subjects | route to the matching Failure-edge routing row | escalate with the receipt quoted verbatim |
| a claim branch and its subject Issue state disagree | route to the matching Failure-edge routing row | escalate; never repair claims from monitor mode |

### Red lines

- Monitor judgments are N/P-class: steer and escalate only, never gate. Landing authority stays with trusted verify.
- Every escalation quotes machine receipts verbatim. A re-derived causal story is not a receipt.
- A steer fires only on a signal from the trigger table. Never on taste.
- Sole-entrypoint boundary: route bundles are evaluation data here, never an action program. A monitor that starts acting along a route has become a second executor bypassing the entrypoint.
- Stage-boundary steering: deliver a steer only at a route stage transition, never mid-stage, so it never competes with the route's own instructions for authority. A signal that cannot wait for the next boundary is not a steer — it belongs to the escalation channel or to a sandbox wall.
- Digest handshake: a steer carries the digest of the bundle it cites; a mismatch against the digest recorded in the executor's session forbids the steer. A stale rubric is worse than silence.
- One delivery per boundary: readers write to a shared queue and a deterministic aggregator dedupes and caps by severity, so at most one delivery reaches the executor per boundary.
- Plural-capable, single-deployed: readers may partition this trigger table into angles under a deterministic angle→reader map, so an unassigned or double-claimed angle fails the monitor configuration check. Deploy one reader until a measured receipt shows a trigger missed through context saturation.

### Steer form

Gate-shaped steering is invalid — it asserts a correctness verdict monitor mode has no authority to assert:

```text
This branch is wrong. Do not merge; the verification is invalid.
```

The valid form quotes a receipt and redirects with a question, at a stage boundary, carrying the cited bundle digest:

```text
bundle <digest>, stage boundary <n>
receipt: "<verbatim line from the run or session record>"
That receipt names a head other than the current branch tip. Which head is this stage proving?
```

## Hard constraints

- Never infer feature ownership from a code path alone.
- Never silently update the frozen source commit.
- Never count an unavailable runtime or provider as verified.
- Never bypass the declared control boundary with direct state-file mutation.
- Never use a mutable upstream checkout path as an adapter dependency.
- Never claim live behavior from schemas, fixtures, unit tests, or hosted repository checks.

## Soft conventions

- Prefer exact subject identifiers over ambient current state.
- Prefer supported CLI/control operations over internal mutation.
- Prefer stable terminal polling and readback over sleeps.
- Prefer the smallest risk-complete journey set compiled from changed edges.

## Discoverable knowledge

Current order IDs, worktree paths, session IDs, PR heads, provider state, credentials, ports, and runtime availability are discovered per execution. Do not promote them into the maintained map from one observation.

## Hermetic authoring

Run the composed validator through the repository suite. Hermetic results establish contract behavior only. If a live dependency is absent, retain the nearest reachable path and residual uncertainty, then stop at the correct evidence ceiling.
