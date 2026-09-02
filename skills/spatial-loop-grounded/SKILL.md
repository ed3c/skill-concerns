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

## Concern layers and roles

Three METHOD layers — a different axis from the Compilation stages C0/C1/C2
and from Shadow severity S0/S1/S2; the numbering schemes must never be mixed:

- L0 procedural — [`references/portable-supervision-kernel.md`](references/portable-supervision-kernel.md):
  the clause kernels, domain-free, one per clause.
- L1 domain knowledge — [`domain/machine-topology.json`](domain/machine-topology.json):
  the machine primitives the clauses' receipts depend on, each self-defined
  (what it is, who owns it, what it writes); rely only on primitives defined
  there, never on undocumented organizational knowledge.
- L2 execution + assertions — [`scripts/validate_spatial_loop_grounded.py`](scripts/validate_spatial_loop_grounded.py)
  and the behavioral eval campaigns under [`evals/`](evals/): form, binding,
  and behavior are asserted, not narrated.

Roles: **BUILD** executes under these clauses (quarantine packets,
salvage-first teardown, terminal readback before consequence). **SHADOW**
supervises reader-only per C1 and reports at stage boundaries with severities
S0 observe / S1 warn / S2 review; a signal that cannot wait for a boundary
goes to the escalation channel, never into steering.

## C1. Monitor is a reader, never a writer

- Signal: any supervising role (shadow architect, fleet monitor, reviewer agent) is being designed or is about to intervene.
- Action: the monitor consumes the SAME skill bytes as the actor (read-only, digest-bound), steers only at material stage boundaries, in receipt-quote + question form; signals that cannot wait for a boundary go to the escalation channel or a wall, never to steering. N/P-class judgments never gate; landing authority stays with the trusted verifier.
- Why: a full session of operator-as-monitor caught scope drift and red-test exits minutes in, while every attempted correctness shortcut through the reader was rejected; the monitor contract survived plurality and pstack-interaction review.
- evidence: monitor-contract, monitor-clauses, monitor-efficacy

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
- Exit when the catch-up atom cannot live in the candidate: prove the in-candidate exit structurally unavailable rather than assuming it (the gate reads its authorization only from the trusted default-branch checkout, so the data cannot ride in the tree being graded), then escalate quarantine-shaped to the gate owner - a receipt naming the gate, its refusal string verbatim, and that structural reason, filed where the owner reads it - and end the lane honestly unmerged. Touch no gate file. The authorization the receipt asks for is legal only byte-pinned to the exact reviewed subject (a sha256, never a standing key for a name) and retired by the landing it buys (the commit that lands the bundle deletes it); a typed exit with no pinned subject and no expiry is a waiver wearing a type, not this exit, and inconvenience is never the trigger.
- Why: five invalid-state classes were eliminated in one session at the architecture layer, and when the surface gate correctly refused three in-flight siblings, a one-line map-revision atom (not a gate rollback) unblocked them within the hour; the escalation exit itself then ran end to end twice, each time as a pinned trusted-side entry that the landing it authorized deleted in the same commit, with no gate file edited in any of the four landings.
- evidence: invalid-state-eliminations, map-revision-protocol, structural-exit-bootstrap

## C8. Bind every action to its exact subject

- Signal: selecting anything by recency or position (latest run, newest branch, current head) before acting on it.
- Action: bind the action to the exact subject identity (head SHA, run id + workflow name, issue number + marker readback) and assert the binding immediately before acting; acting on a stale subject is forbidden even when the action itself is benign - a rerun of a stale run cancels the live head's run.
- Why: the stale-rerun hazard and the watched-wrong-workflow incident were both position-selection failures; the identity-bound forms of the same commands have not misfired since.
- evidence: exact-subject, stale-rerun-guard

## C9. An oldest-first queue starves behind a permanently failing head

- Signal: a mechanical queue serves oldest-eligible-first, and its current head keeps re-entering eligibility (rebases clean, goes behind again after every advance) while never reaching its terminal (verification stays red without owner action).
- Action: park the head honestly by correcting its state to what it mechanically is (blocked, not ready-to-land) so selection skips it; then cure the selection rule itself with its own atom (skip a head whose current identity already carries a completed failure); never hand-serve the starved items as the standing fix.
- Why: an oldest-first landing rebaser re-selected the same clean-rebasing, verify-failing head after every land — main advanced, the head went behind again, got re-picked — and every newer ready item starved; parking the head to blocked freed the queue within one cycle and the selection-rule cure was filed as its own atom.
- evidence: train-starvation

## C10. No completion notification means still running

- Signal: dispatched background work looks dead — no result artifact, no process found, no progress visible — and manual takeover of its outputs is about to start.
- Action: treat the harness completion notification as the only death certificate; missing artifacts, absence from process lists, and silence are all consistent with still-running. If intervention already happened, lease-guarded writes are what keep the still-running owner and the intervenor from destroying each other's work.
- Why: a dispatch run was declared crashed on three absence signals and its branches were hand-landed — while it was still running; lease discipline plus patch-id deduplication absorbed the collision and the run's own agents landed improved versions on top of the manual rebase.
- evidence: still-running-not-crashed

## C11. Exit-code residue is not current state

- Signal: a scheduler or launcher displays a nonzero last-exit status for a job, and the job is about to be declared unhealthy (or healthy, on a zero).
- Action: judge health only from the job's terminal log line plus direct readback of the artifact the job exists to produce; a residual status describes one past run, and a later successful run may not clear it.
- Why: a launcher listed exit 1 for a nightly job while the job's own log ended with a full-success line and both of its produced artifacts read back complete — the residue came from an earlier attempt that a later run had already superseded.
- evidence: exit-residue

## Non-claims

- This skill does not restate the upstream spatial-loop body (ICPG, complexity classes, constraint compiler); consult upstream for method, this skill for what survived contact.
- Receipts prove the clauses fired in one repository-machine environment (ed3c/noodles, 2026-08-30/31), plus one host-scheduler receipt for C11 — a second environment class. Portability beyond these carries new receipts or stays a hypothesis.
