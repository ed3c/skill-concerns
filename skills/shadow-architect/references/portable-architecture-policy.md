# Portable architecture policy — L0 procedural

L0 procedural: one kernel per clause, domain-free. Every kernel below is a
decision rule about the SHAPE of a change. None of them names a repository, a
host, a tool, a file in this bundle, or a provider. The instantiation — which
precedent was earned where, against which judged diff, with which detector —
lives in the domain ledger next to this document, and the entry document is
what binds the two.

A monitor carrying these kernels reads a diff and asks. It does not decide.
Every kernel's output is a question with the bytes that raised it quoted
beside it, because a judgement about shape is only worth as much as the bytes
it can point at, and because the person who wrote the change is the one who
knows whether the answer exists.

- K1 A declared thing that nothing resolves is not documentation; it is a
  claim with no reader. Before adding a field, a key, an option or an
  abstraction, name the process that consumes it. If the only consumer is the
  code that validates the thing's own shape, the thing is not being used, it
  is being guarded — delete it rather than demoting it to a comment, and let
  the record that motivated it carry the motivation.
- K2 A mechanism that needs prose to read as correct is where the escape
  lives. Prefer the spelling whose correctness is visible in the expression
  itself over the spelling whose correctness depends on a reader holding an
  invariant in mind. A test on a name is a binding only when the name cannot
  lie about what it points at.
- K3 A second literal of a set that already exists will drift, and both
  readings will look right while it does. When two places must agree, one of
  them derives from the other; when a checker needs the members of a set, it
  reads them from the declaration that owns them rather than carrying a copy
  it must remember to update.
- K4 Availability is not use. A convention that only an author's memory
  re-reads is a defect of shape, not of discipline: it will hold while the
  author is present and decay silently afterwards. When a mechanical value and
  the prose describing it live side by side, a rename moves the value and
  leaves the prose, so the cure is a reader over the prose rather than a
  more careful pass.
- K5 The smallest change that satisfies the requirement, and no gate widened
  to fit it. A rule that refuses a candidate mid-flight is satisfied through
  the candidate's own data, never by moving the rule or its predicate; the
  atom that moves a rule is a separate, separately reviewed change, because
  the reviewer of the first cannot see what the second bought.
- K6 An entry that covers another owner's procedure points at it and never
  restates it. A restated copy reads as agreement on the day it is written and
  becomes disagreement the day the owner changes, with nothing between the two
  that goes red. One concern, one owner, one set of bytes.
- K7 Ambient is not admitted. A dependency read from an unpinned location —
  a path on the machine, a tool on the search path, a document at whatever
  version happens to be there — is ambient: its version is unknown, its drift
  is invisible, and a failure looks like the dependency refusing rather than
  like the wrong bytes arriving. Admitted means content-addressed bytes some
  process re-resolves on a schedule.
