---
name: spatial-loop-grounded
description: >
  The environment-evidenced subset of spatial-loop-systems-engineering.
  Use when supervising or executing agent-driven repository machines and a
  clause is needed that has already survived physical contact: every clause
  below carries exact receipts from the 2026-08-30/31 ed3c/noodles session
  and a hollow-mutation eval. Clauses without receipts are not here; the
  upstream skills-shared body remains the method owner.
---

# Spatial Loop, Grounded

Provenance: upstream method is `skills-shared/skills/spatial-loop-systems-engineering`
(registry status: method ownership only; live receipts environment-owned).
This skill admits ONLY clauses with session receipts, pinned in
[`receipts.json`](receipts.json). The eval suite fails closed if any clause
loses its trigger form or its receipt binding.

## Clause form

Every clause is trigger-shaped: **Signal** (when to think of it) →
**Action** (what to do) → **Why** (the receipt that proves it) →
`evidence:` (ids resolved against receipts.json).

## C1. Monitor is a reader, never a writer

- Signal: any supervising role (shadow architect, fleet monitor, reviewer agent) is being designed or is about to intervene.
- Action: the monitor consumes the SAME skill bytes as the actor (read-only, digest-bound), steers only at material stage boundaries, in receipt-quote + question form; signals that cannot wait for a boundary go to the escalation channel or a wall, never to steering. N/P-class judgments never gate; landing authority stays with the trusted verifier.
- Why: a full session of operator-as-monitor caught scope drift and red-test exits minutes in, while every attempted correctness shortcut through the reader was rejected; the monitor contract survived plurality and pstack-interaction review.
- evidence: monitor-contract, monitor-clauses

## C2. Count decompression layers before any claim

- Signal: about to assert "verified", "available", "already claimed", "completed", or any property read off a representation (a name, a flag, a run row, an exit code, stdout text).
- Action: count the decompression layers between the checked representation and the claimed property; each layer must be eliminated (bind judgment to terminal state; selectors carry identity, not just position), semantics-carried (the emitter ships the meaning with the value; digest-bind shared standards), or negative-controlled (a standard that has never refused anything is not physical). Verifying a true premise is not verifying the load-bearing premise.
- Why: one session produced eight incidents all reducible to this gap - a status word misread for hours, a plan gate checked instead of an ownership gate, a wrong workflow watched by position, byte-identical trees red-then-green exposing flake-as-causation.
- evidence: receipt-semantics, ownership-premise, decompression-law

## C3. FIRST_GREEN is a review point, not a completion

- Signal: a success signal just arrived (watch exited 0, suite green, command returned) and a consequential action (sweep, delete, announce, promote) is about to follow.
- Action: assert the terminal state by direct readback before the consequential action (MERGED before branch delete; issue CLOSED before completion claims); a green mid-chain signal authorizes nothing downstream of it.
- Why: one sweep executed on a watch-exit instead of a MERGED readback closed an open PR and cost a full re-land cycle; the corrected ceremony (terminal readback first) landed the same atom cleanly.
- evidence: premature-sweep, terminal-readback

## C4. Repeated failure escalates to a quarantine packet

- Signal: the same target has failed the same way three or more times, and the next attempt would repeat the previous shape.
- Action: stop blind repair; quarantine the target with a receipt naming the observed death pattern and the explicit unblock conditions; reroute the fleet around it; file the diagnosis where its owner will find it.
- Why: one atom whose every admission killed the daemon within minutes (four instances) froze the whole fleet in a perfect loop until quarantined with a blocker receipt; the fleet resumed on the next cycle.
- evidence: poison-pill
- escalation: after quarantine, apply the upstream repair topology - fresh diagnosis, new isolated worktree - never resume in the contaminated context.

## C5. Evidence regenerates through its producer, never by hand

- Signal: a recorded receipt, fixture, or evidence artifact disagrees with the current tree (drift after rebase, count mismatch, stale binding).
- Action: regenerate the artifact by running its own producer against the current subject; hand-editing evidence is laundering even when the edit would be factually right. If freshness of any recorded fact is in doubt, regenerate again after the subject moves.
- Why: an evidence receipt recording 3 symbol candidates went stale when the tree gained a 4th; the repair agent reran the pinned probe twice - once more after a further rebase purely so a recorded line number stayed factually true - and landed clean.
- evidence: producer-regeneration

## C6. Teardown mirrors construction, gated on terminal readback

- Signal: any destructive symmetric action (delete the branch you pushed, remove the claim you created, clear the state you set).
- Action: the teardown fires only after the terminal state that justifies it is read back from the authority (provider truth), and never deletes what a live process still owns; when in doubt, salvage to a named ref first - push the bytes somewhere durable, then reset.
- Why: auto-salvage-then-reset turned a repeated fleet-wedging failure class into an 11-second self-heal; every deletion in the session that followed MERGED-readback was safe, and the one that did not caused the C3 incident.
- evidence: salvage-heal, premature-sweep

## C7. Newly reachable invalid states are first-class deltas

- Signal: a failure recurs, a review comment repeats, or a new gate/feature lands while siblings are in flight.
- Action: classify the failure into the enforcement hierarchy and sink it to the strongest layer that holds it (architecture > CI > lint > rules); when a new gate outruns in-flight work, the gate stays and the admission data catches up via its own atom - candidates must never widen the surface they are judged against.
- Why: five invalid-state classes were eliminated in one session at the architecture layer, and when the surface gate correctly refused three in-flight siblings, a one-line map-revision atom (not a gate rollback) unblocked them within the hour.
- evidence: invalid-state-eliminations, map-revision-protocol

## C8. Bind every action to its exact subject

- Signal: selecting anything by recency or position (latest run, newest branch, current head) before acting on it.
- Action: bind the action to the exact subject identity (head SHA, run id + workflow name, issue number + marker readback) and assert the binding immediately before acting; acting on a stale subject is forbidden even when the action itself is benign - a rerun of a stale run cancels the live head's run.
- Why: the stale-rerun hazard and the watched-wrong-workflow incident were both position-selection failures; the identity-bound forms of the same commands have not misfired since.
- evidence: exact-subject, stale-rerun-guard

## Non-claims

- This skill does not restate the upstream spatial-loop body (ICPG, complexity classes, constraint compiler); consult upstream for method, this skill for what survived contact.
- Receipts prove the clauses fired in ONE environment (ed3c/noodles, 2026-08-30/31); portability beyond machine-ceremony repositories is a hypothesis until new receipts exist.
