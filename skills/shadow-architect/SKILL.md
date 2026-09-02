---
name: shadow-architect
description: >
  Judge the architecture shape of a change at a stage boundary against a pinned
  ledger of precedents wave monitors have actually issued: match a diff's added
  bytes, quote what matched, and hand back numbered questions with the wave
  receipt that grounded each one. Use at a wave or generation boundary, on a
  lane's diff before it lands, or whenever "is this over-built?" needs an
  answer somebody can check. Reader-only against every subject; it decides
  nothing and files nothing.
---

# Shadow Architect

The architecture angle of the wave monitor used to be an ambient dependency: a
prompt line pointing at a directory on one machine, at whatever version was
there, with no pin and no digest — the exact shape clause P7 below refuses. This
bundle is that angle as admitted bytes. The extraction is bounded on purpose:
only the principles wave monitors actually cited are here, each pinned to the
wave receipt that recorded it and to the real judged diff it was issued against.

Roles: **BUILD** is the only half that changes the ledger — one adjudicated
precedent at a time, behind the repository's cure-authorization refusal, landing
through the PR ceremony. **SHADOW** is reader-only: it matches, quotes, and asks
at severities S0 observe / S1 warn / S2 review, and never writes into the subject
it reads. A SHADOW pass whose subject digest moved refuses its own report.

## The precedent ledger - pinned bytes, one wave receipt per clause

[`domain/precedents.json`](domain/precedents.json) is read at a commit, never
remembered. Each precedent carries:

- **provenance** — the wave label where one is recorded, the monitor record that
  wrote the finding down, the provider receipts that ground it, and the commit
  whose diff it was issued against;
- **a detector** — a signal a machine can run over a diff's added lines, and the
  acquittal that clears it, scoped to the added lines of the file it clears: an
  exculpation is a claim about one file's own bytes, so no single incantation
  anywhere in a diff can silence a clause across every file the diff touches;
- **a fixture and a control** — the real judged diff where the finding was made,
  and a real diff where the same clause must stay silent.

Both directions are mechanical. A clause whose own fixture does not raise it is
`PRECEDENT_FIXTURE_SILENT`; a clause raised by the diff that cured it is
`PRECEDENT_CONTROL_NOISY`. A ledger of rules nobody ever saw fire is a ledger of
opinions, and the fixture is what keeps this one out of that shape.

The wave label is quoted from the record named in `monitor_record`; nothing here
re-resolves a commit or a ledger at run time. That is the cadence sweep's job,
through the provider refs in [`receipts.json`](receipts.json).

## Clause form

Every clause is trigger-shaped: **Signal** (when to think of it) ->
**Action** (what to ask) -> **Why** (the finding that earned it) ->
`provenance:` (the monitor record, verbatim) ->
`evidence:` (ids resolved against [`receipts.json`](receipts.json)).

## P1. An abstraction, field or config key no process resolves

- Signal: a change adds a field, an option, an interface or a layer, and the reviewer is about to accept it because the shape looks tidy.
- Action: ask which process resolves it, and require the answer to be a path. If the only bytes that mention it are the bytes that validate its own shape, it is guarded rather than used; delete it instead of demoting it to a comment, and let the record that motivated it carry the motivation.
- Why: a first-admission allowlist landed with two fields validated by their own diagnostics and read by nothing; a grep of the branch found each one only inside its own validation.
- provenance: wave-17 / commit:f0cf0803d5981111f60e439afaa6c04bdb3a2492
- evidence: P1

## P2. Boring over clever: a mechanism that needs an explanation to read as correct

- Signal: the correctness of an added check depends on the reader holding an invariant in mind while reading it.
- Action: ask what makes the expression correct on its own bytes, and prefer the spelling whose correctness is visible in the expression. A test on a name is a binding only when the name cannot lie about what it points at.
- Why: the same allowlist bound an authorization to a Skill's own tree with a prefix test that a relative-parent segment walked straight out of; the check read as correct and admitted anything in the tree.
- provenance: wave-17 / commit:f0cf0803d5981111f60e439afaa6c04bdb3a2492
- evidence: P2

## P3. The stale list: a second literal of a set that already exists

- Signal: a module declares a constant, a pattern or a membership list that another module in the same tree already owns.
- Action: ask which declaration owns the identity and make the second one derive from it or import it. When a checker needs the members of a set, it reads them from the declaration that owns them; a per-subject list inside a generic gate is the same defect one level up.
- Why: a repository-wide conformance gate landed carrying its own private copy of an identity pattern the shared module had introduced two atoms earlier — two literals of one shape, and both readings looked right.
- provenance: commit:b7827d58fb85e5dc2cccaa9f09114e42992e9dcc
- evidence: P3

## P4. Availability is not use: a convention only author memory re-reads

- Signal: a change moves a machine-read value and leaves the prose that describes it, or lands a convention an issue could enumerate and nothing re-reads.
- Action: ask what reads the prose. A convention with no reader holds while its author is present and decays silently afterwards, so the cure is a reader over the prose rather than a promise of a more careful pass.
- Why: renaming an arrival axis moved every machine-read column mechanically and left three row notes still reasoning in the retired numbering — true sentences about a vocabulary the ledger had just stopped owning, inside the ledger whose own clause names that shape.
- provenance: commit:2e59255a580b291b54a294bfce722564416d16bc
- evidence: P4

## P5. The smallest diff that satisfies the issue, and no gate widened to fit it

- Signal: the atom that needs a rule relaxed is the atom that relaxes it.
- Action: ask whether the requirement can be satisfied through the candidate's own data instead, leaving the rule untouched. Moving a rule is a separate, separately reviewed change, because the reviewer of the first cannot see what the second bought.
- Why: an atom changed a gate's expected value and the data that value checks in one landing; the gate that graded it was the older copy on the default branch, which still demanded the old value, and every receipt in the tree went red at once.
- provenance: commit:65e1b41c4e03e0551682b305ba6566b74f7719e8
- evidence: P5

## P6. A restated copy of another owner's ceremony, where a pointer belongs

- Signal: a module's own bytes explain an adjudication, a ceremony or a contract that a different document owns.
- Action: ask for the pointer. A restated copy reads as agreement on the day it is written and becomes disagreement the day the owner changes, with nothing between the two that goes red.
- Why: a loop's module docstring restated three adjudications in full prose with no mechanical reader of its own — the exact anti-pattern the document it copied from names in its own bytes.
- provenance: wave-14 / commit:aaf05089cd7b6e738068561d25e586f938b9b47f
- evidence: P6

## P7. Ambient versus admitted: a dependency with no pin and no digest

- Signal: a change reaches a host path, a tool on the search path, or a document at whatever version happens to be there.
- Action: ask which bytes it reads and what re-resolves them. A one-time readback probe is an observation, not a reader; admitted means content-addressed bytes some process re-resolves on a schedule.
- Why: a behavioural campaign's control arm was driven by a host command whose floor depended on that machine's settings; the settings were readback-probed once, with no standing reader, so a re-run on a differently configured host would move the arm with nothing going red.
- provenance: 2026-09-01-ab-control-arm / ledger:2026-09-01-ab-control-arm
- evidence: P7

## Diagnostics

The driver and its validator emit exactly these, and only these:

- `PRECEDENT_WITHOUT_PROVENANCE` — a clause with no wave receipt and no monitor quote behind it.
- `PRECEDENT_FIXTURE_SILENT` — a clause whose own grounding diff does not raise it.
- `PRECEDENT_CONTROL_NOISY` — a clause raised by the diff that cured it.
- `CLAUSE_WITHOUT_PRECEDENT` — an entry-document clause with no ledger entry, or a ledger entry with no clause.
- `PROVENANCE_RECORD_UNBOUND` — a provenance whose subject commit is not the commit the fixture's own bytes name.
- `SUBJECT_MUTATED` — the subject digest moved during a reader-only pass; the report is untrusted.
- `FINDING_MALFORMED` — a finding the schema rejects: no quoted bytes, no question, or a subject bound to no digest.
- `DRIVER_SURFACE_FORBIDDEN` — a module in this bundle imports a way to spawn a process or open a socket.
- `ANSWER_KEY_VISIBLE` — a script in this bundle names the campaign answer key, so the planted arm would no longer be blind.
- `BUILD_CURE_UNAUTHORIZED` — a precedent folded in with no cure-authorization. The rule and its decision live once in the repository's shared implementation, which every BUILD carrier calls.

## Knowledge placement

Concern layers:

- L0 procedural — [`references/portable-architecture-policy.md`](references/portable-architecture-policy.md): one domain-free kernel per clause.
- L1 domain knowledge — [`domain/precedents.json`](domain/precedents.json): the precedents, their provenance, their detectors, and the real judged diffs under [`evals/fixtures/waves/`](evals/fixtures/waves/).
- L2 execution + assertions — [`scripts/shadow_driver.py`](scripts/shadow_driver.py) and [`scripts/validate_shadow_architect.py`](scripts/validate_shadow_architect.py), plus the planted campaign arm under [`evals/fixtures/planted/`](evals/fixtures/planted/).

Arrival is tracked as a row in the repository's capability topology, not claimed
here: the arrival vocabulary belongs to the bundle that owns it, and this one
references it rather than restating it — which is clause P6 applied to this
document. The row rises to production arrival when a wave monitor's own findings
cite these clauses by digest-pinned path.

```sh
python3 skills/shadow-architect/scripts/shadow_driver.py --diff <path>              # SHADOW: reader-only
python3 skills/shadow-architect/scripts/shadow_driver.py --diff <path> --render     # the issue-body block
python3 skills/shadow-architect/scripts/shadow_driver.py --diff <path> --clause P3  # one precedent
python3 skills/shadow-architect/scripts/validate_shadow_architect.py [--selftest]
python3 skills/shadow-architect/scripts/gen_shadow_receipts.py                      # receipts.json's only author
```

## Non-claims

- No verdicts. Every finding is a question with the bytes that raised it quoted beside it; a signal is a reason to ask, never a proof, and the person who wrote the change is the one who knows whether the answer exists. A finding with no question is refused by the schema.
- No blocking rung, dropped rather than mislaid. The host prompt this angle was read from ran a four-rung intervention ladder — `L0 OBSERVE`, `L1 WARN`, `L2 REVIEW_BEFORE_NEXT_CHECKPOINT`, `L3 BLOCK_NAMED_TRANSITION` — and five verdicts including `BLOCK_NAMED_TRANSITION` and `ESCALATE_HUMAN`. Three severities land here and no verdict does. Blocking a transition is stop authority, which belongs to the dispatcher and to nothing this bundle can reach; a rung a reader-only pass could name but never exercise is an option no process resolves, which is clause P1 aimed at this document. The dropped rung is recorded here so a later reader finds a decision rather than an omission.
- No experiments against the subject. The falsification verb — rewrite-all-to-the-exit, planted-direction replay, producer re-runs in throwaway clones — belongs to `red-team`, which owns it. This bundle reads and asks; that one executes. The differential is the verb, and it is deliberate.
- No fourth judgment angle either. `spatial-loop-grounded` issues clause verdicts over supervised conduct, `context-closure-engineering` compiles and checks one bounded context projection, `dynamic-workflow` classifies runtime liveness of dispatch lanes, and `arrival-engineering` audits the capability wiring graph at rest. This one judges the shape of a change.
- No filing. Nothing here creates, edits, comments on, closes or merges anything at a provider. `DRIVER_SURFACE_FORBIDDEN` is what keeps that true rather than the sentence that claims it: no module in this bundle may import a way to spawn a process or open a socket, which is the property one level under any list of forbidden verbs.
- No autonomous ledger growth. A precedent enters only from an adjudicated verdict — a clause IS an enforcement shape, so the cure-authorization refusal is unconditional, and a detection never authorizes the clause it detects.
- No wholesale import. The extraction is bounded to the principles wave monitors actually cited, with receipts; the fate of the directory this angle used to be read from is the operator's and is out of scope here.
- No completed decoupling. This bundle is the pinned source; the standing dispatch formula's wave-route line is the dispatcher's to switch, and until it is switched the monitor still reads the ambient path. That switch is the decoupling's completion criterion and it is recorded on the admission issue, not claimed here.
