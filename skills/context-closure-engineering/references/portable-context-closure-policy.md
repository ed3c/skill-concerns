# Portable context-closure policy (L0 procedural)

Domain-decoupled laws for compiling long, mixed source material into a bounded
projection that a later Agent can read without re-deriving the program from the
most recent prompt. They hold for any repository, provider, or document set; the
concrete file names, source identities, and vocabularies belong to the L1
domain layer, not here.

The law set is closed and count-tied: the L1 topology declares how many laws
exist and their exact ids, and the validator refuses a silent addition or
deletion on both the count and the id set. A law is one clause, not an essay.

## LAW-DENOMINATOR

Every source enters the frozen denominator exactly once and never leaves it;
material whose bytes or identity are unavailable stays in the denominator marked
absent or unknown-current instead of disappearing from the accounting.

## LAW-ANCHOR

Every nontrivial statement carries one exact source id and one classification,
so a reader can walk from any sentence back to the bytes it came from.

## LAW-NO-PROMOTION

Authority classes are not confidence scores: repetition, agreement between
sources, or placement in an important-looking document never promotes a
statement, and a projection's own sentences stay at projection or procedure
authority no matter what they point at.

## LAW-EDGE-SPLIT

Start-readiness never satisfies a completion edge; a lifecycle marker, a
scheduler's notion of runnable, a start edge, and a completion edge are four
different facts that must stay separately named.

## LAW-ONE-CONVERGENCE-OWNER

Every durable value and every active write boundary has exactly one convergence
owner; two owners for one value is a finding, not a merge to resolve later.

## LAW-TRACE-GAP

A missing segment of a chain is recorded as a traceability gap; a nearby task, a
commit message, a closed provider object, or an Agent's memory may not fill it.

## LAW-NO-MUTATION

The projection is dated output, never an actor: it does not create, close,
merge, schedule, or otherwise mutate the state it describes, and it never
appears as the evidence backing a completion claim.

## LAW-EXTERNAL-CLAIM

An article, PDF, image, screenshot, post, or model consensus stays an external
claim until a separate primary-source receipt binds it; the projection may carry
the claim and its absence, not its truth.
