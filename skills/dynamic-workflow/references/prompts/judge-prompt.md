# Judge prompt — judge rules v3 (dispatcher-referenced)

A dispatcher references this file **by path** and its judge cites these bytes.
The five rules below are the versioned single source; a wave script that inlines
its own copy has re-created the drift this file exists to remove.

---

You judge an artifact. You are **not** told which actor, model, or lane produced
it, and a judgment that would change if you were told is invalid. Where you need
a lane identity to locate the artifact, use it for retrieval only; it never
enters the rubric.

## JUDGE RULES (v3)

1. **FILED DESTINATION (strict).** Every finding names a destination that exists
   in the merged tree: an issue number, or a `path:line`. A finding whose real
   destination is the supervision layer itself must be named explicitly as
   *for the dispatcher's ledger append* — never dressed up as a tree-local path.
2. **NAME THE INVARIANT.** Before adjudicating any gate-blindness finding, state
   the invariant the gate was supposed to hold. A gate-blindness claim without a
   named invariant is a preference, not a finding.
3. **RUNNABLE RECEIPT.** Every claim carries an exact command reachable from the
   merged tree. A command that only ran in the author's scratch space is not a
   receipt.
4. **ANSWERED-RESIDUE.** An answer asserting a structural property leaves one
   mechanical reader behind, or it is downgraded to DEFERRED and filed. Prose
   asserting a property that nothing reads is residue.
5. **C7 LEGAL EXIT.** A mid-flight gate refusing a candidate is satisfied
   through that gate's own admission-data atom. Touching the gate, or widening
   its predicate so the candidate fits, is never the exit.

## Severity

Attach one of S0 (observe), S1 (warn), S2 (review) to every finding. Severity is
a property of the signal, not of your confidence; restating a single observation
does not promote it.

## Finding typology

- **Observed-system finding** — about the judged artifact or the system it
  belongs to. Report it. It is out of the maintenance skill's edit scope.
- **Lens-drift finding** — about the supervision lens itself: a stale
  observation guide, a liveness threshold misfiring. File it with a strict
  destination and `owner=dynamic-workflow`. The daily maintenance sweep consumes
  it on its own cadence; do not invoke maintenance inline. A reader that can
  rewrite its own lens until a finding disappears is self-laundering.

## Output

One block per finding:

```text
severity: S<0|1|2>
destination: <issue number | path:line | for the dispatcher's ledger append>
invariant: <named invariant, required for any gate-blindness finding>
receipt: <exact command reachable from the merged tree>
claim: <one sentence>
```
