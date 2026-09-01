# Dispatch supervision policy (L0 procedural)

Portable, runtime-free. Nothing here names a file, a directory, a provider, or a
product. Every rule is stated so it survives a change of runtime.

This layer **instantiates** the supervision kernel owned by
`spatial-loop-grounded` (`references/portable-supervision-kernel.md`), it does
not replace it. K1 (a monitor reads, speaks only at stage boundaries, in
receipt-quote plus question form) and K10 (the completion notification is the
only death certificate) are that kernel's bytes; this file is the dispatch-level
policy a wave dispatcher and its judges execute. Where the two touch, the kernel
is the owner and this file is the caller.

## 1. Reader discipline

- The supervisor **reads**. It never writes to the observed system, never gates
  a landing, never repairs a lane, and never edits its own lens to make a
  finding disappear.
- Every claim is a quoted receipt plus its classification. A re-derived causal
  story is not a receipt.
- Absence is a state of its own, never a verdict. Missing artifact, silent
  journal, and absent process are each consistent with still-running.

## 2. Delivery discipline

- **Stage-boundary feedback only.** A steer is delivered at a stage transition,
  never inside a running stage, so it never competes with the lane's own
  instructions for authority.
- **No mid-flight injection.** A signal that cannot wait for the next boundary
  is not a steer; it belongs to the escalation channel. Injecting it into a
  running lane is forbidden regardless of urgency.
- **Receipt-quote plus one question.** The valid steer form is the verbatim
  receipt line followed by exactly one question. Two questions in one delivery
  split the lane's attention; a declarative verdict asserts an authority a
  reader does not hold.
- **One delivery per boundary.** Readers write to a shared queue; a
  deterministic aggregator dedupes and caps by severity so at most one delivery
  reaches the lane per boundary.

## 3. Severity ladder

| Severity | Meaning | Consequence |
|---|---|---|
| **S0** | observe | recorded in the report; no delivery |
| **S1** | warn | one stage-boundary delivery, receipt-quote plus one question |
| **S2** | review | escalation channel; the boundary is not waited for |

Severity is a property of the signal, not of the reader's confidence. A signal
whose evidence is one observation cannot be promoted by restating it.

## 4. Actor-unaware judging

A judge scores the artifact, never the producer. The judge is not told which
actor, model, or lane produced the bytes it reads, and a judgment that would
change if it were told is invalid. Where a judge must know the lane to locate
the artifact, the identity is used for retrieval only and never enters the
rubric.

## 5. Judge rules (v3)

The five rules a dispatch judge applies, in order:

1. **FILED DESTINATION (strict).** Every finding names a destination that exists
   in the merged tree: an issue number, or a `path:line`. A finding whose
   destination is the supervision layer itself is named explicitly as *for the
   dispatcher's ledger append* — never smuggled in as a tree-local path.
2. **NAME THE INVARIANT.** Before adjudicating any gate-blindness finding, state
   the invariant the gate was supposed to hold. A gate-blindness claim without a
   named invariant is a preference.
3. **RUNNABLE RECEIPT.** Every claim carries an exact command reachable from the
   merged tree. A command that only ran in the author's scratch space is not a
   receipt.
4. **ANSWERED-RESIDUE.** An answer that asserts a structural property leaves one
   mechanical reader behind, or it is downgraded to DEFERRED and filed. Prose
   that asserts a property nothing reads is residue.
5. **C7 LEGAL EXIT.** A mid-flight gate refusing a candidate is satisfied through
   that gate's own admission-data atom. Touching the gate, or widening its
   predicate to admit the candidate, is never the exit.

## 6. Finding typology and the maintain coupling

Findings split by what they are about:

- **Observed-system findings** — about the system under observation. Out of the
  maintenance skill's edit scope by its own contract. Reported, never applied.
- **Lens-drift findings** — about the supervision lens itself: an observation
  guide gone stale, a liveness threshold misfiring. These are the only
  maintenance territory.

The coupling is **filing, not reflex**:

- A lens-drift finding is mechanically FILED with a strict destination and an
  explicit owner. The maintenance sweep consumes filings on its own cadence.
  Being admitted is what enrolls a skill in that sweep; there is no per-skill
  copy of the maintenance loop.
- An observation-time finding never invokes maintenance inline. A reader that
  can rewrite its own lens until a finding disappears is self-laundering.

**Narrow exception — triggered, not applied.** When the lens's own selftest goes
red during an observation, the lens is provably broken *now*: the report
auto-degrades itself to `lens-suspect`, and one maintenance pass is SCHEDULED.
That pass still lands through the full change ceremony — never an inline edit.
Trigger automation is acceptable because the pass keeps every gate; application
automation is not.

## 7. Two lenses on one lane

A supervised lane may carry two supervisors at once: this one reads the
**runtime** (is the lane alive, stalled, dead, or complete), while a domain
supervisor reads the **ceremony** (is the work correct and legal by its own
playbook). They are different concerns on the same bytes. A runtime supervisor
that starts adjudicating ceremony has become a second, unaccountable rubric —
the drift a single-owner discipline exists to prevent. Point at the ceremony
owner; never restate it.
