# Source proposal — context-closure-engineering

Owner design brief for `ed3c/skill-concerns#9`. This document is the frozen
proposal; the method bytes it refactors are frozen separately by blob identity
in `source-lock.json` under `method_references`, so this repository carries a
pointer rather than a copy.

## Exact method source

The method exists as six documents materialized by the consumer canary
`ed3c/noodles#117`, at commit `2f926297ab66ae62784bf3f5d7cd3089bc890f1c`, under
`docs/design/context-closure/`: `README.md`, `SYSTEM.md`, `DAG.md`,
`CLOSURE.md`, `TRACEABILITY.md`, `DRIFT.md`. Their blob hashes are the locked
identity. That directory is `N-class` in its own repository: it gates nothing
there, and reading it here grants nothing either.

`ed3c/skill-concerns#9` also names `ed3c/skills-shared@52b29b38...` as a method
reference for the Shadow Architect, Tech Lead, and procedural-runtime roles.
Those roles are referenced by name in the bundle and their procedures are not
copied. The bundle composes them; it does not absorb them.

## What is admitted

A `domain-rich` bundle in three layers:

- **L0 procedural** — eight portable laws, one clause each: denominator,
  anchoring, non-promotion, edge split, single convergence owner, traceability
  gap, non-mutation, external claim.
- **L1 domain knowledge** — the frozen source identity, the six pack roles and
  their default file names, the classification and authority vocabularies, the
  five edge classes, the planted-negative ledger, and the consumer-canary state.
- **L2 execution + assertions** — a checker over a pack directory, with a
  selftest that replays every mechanized planted negative.

## Deterministic controls

The method's own drift ledger lists seven planted negatives and records that
none of them was mechanized. Five are mechanized here:

| Probe | Mechanized as |
|---|---|
| remove one denominator source | `SOURCE_UNDECLARED` |
| replace a completion edge with a start edge | `EDGE_CLASS_COLLAPSE` |
| two active writers for one durable value | `DUPLICATE_WRITER` |
| cite the pack as completion evidence | `EVIDENCE_PROMOTION` |
| delete the absent article/PDF row | `DENOMINATOR_SHRINK` |

Two are not, and are declared `NOT_MECHANIZED` with their owner: a predecessor
read as landed from merge ancestry while its provider marker disagrees, and an
open change with green candidate checks treated as ready while the trusted check
fails. Both need an authenticated readback of current provider state; a hermetic
checker can only compare a frozen observation against itself, which is exactly
the failure they probe.

## Evidence ceiling

`L3_HERMETIC`. Consumer integration at `ed3c/noodles#117` is a separate receipt
this repository does not hold: `consumer_canary.state` is `NOT_EXERCISED`, and
the validator refuses any stronger value from this tree.

## Deviations from #9's literal text

This section exists so the Issue owner can adjudicate these without reading a
lane chat transcript that does not persist past this session. `#9` is left
open by this landing (the PR bodies read `Refs`, not `Closes`) precisely so
these can be reviewed against the merged tree rather than closed unseen.

| #9 asked for | This delivers | Why, and what it costs |
|---|---|---|
| `kind: procedure-rich` | `kind: domain-rich` | `check_skill_bundles.py` forbids `domain_paths` on `procedure-rich`, and an L1 topology (`domain/context-closure-topology.json`) is exactly a `domain_paths` entry. Admitting the topology as designed required `domain-rich`. |
| `method_references` bound to `ed3c/skills-shared@52b29b38…`, paths `spatial-loop-systems-engineering/SKILL.md`, `agentic-tech-lead-orchestration/SKILL.md`, `procedural-shadow-runtime/SKILL.md` | `method_references` bound instead to six `ed3c/noodles` documents under `docs/design/context-closure/` at commit `2f92629…` — the consumer canary's own already-materialized output | **This is the largest deviation.** The three skills-shared Skills are referenced by name in `SKILL.md`/`AGENTS.md` as composed roles, not source-locked or refactored into law clauses. The eight portable laws were instead generalized from the noodles pack's own DRIFT ledger. #9's text names the noodles Issue as the *consumer canary* (where the resulting Skill gets tried), not as the *method source* (which it names as skills-shared). This tree inverts that: it treats the canary's product as the method and the named method as composed-by-reference only. An owner who intended the laws to come from the three skills-shared procedures, not from one example of their output, should treat this admission as not satisfying #9 as written. |
| Classification vocabulary: `REQUIREMENT`, `DESIGN_PROPOSAL`, `ASSUMPTION`, `OBSERVATION`, `MEASURED_FACT`, `EXTERNAL_CLAIM`, `UNKNOWN` (7 terms) | `OWNER_REQUIREMENT`, `REPOSITORY_FACT`, `HISTORICAL_PROVIDER_FACT`, `HISTORICAL_PROJECTION`, `METHOD_SOURCE`, `EXTERNAL_CLAIM`, `L_REFERENCE`, `R_REFERENCE`, `UNKNOWN_CURRENT`, `ABSENT` (10 terms, only `EXTERNAL_CLAIM` shared) | Reshaped around the noodles pack's own five source-family shape (owner/tree/provider/method/external) rather than #9's generic epistemic-status vocabulary. Not a superset or a refinement — a different vocabulary answering a related but distinct question. |
| Required reference files `context-pack-contract.md`, `source-classification.md`, `closure-and-drift-rules.md` | Not present; their content lives in the L1 JSON topology instead | Recorded as a deliberate choice (a prose restatement of the same vocabulary would be a second source of truth), but it means the three named files #9 asked for do not exist under this path. |
| Terminals `CONTRADICTORY_SOURCE`, `PRIVATE_REASONING_REQUESTED`, `CONSUMER_MUTATION_NOT_AUTHORIZED` | None of the three appear anywhere in L2, and none carries a `NOT_MECHANIZED` row the way PN-5/PN-7 do | Unlike the two provider-readback gaps (which are named, owned, and reasoned about), these three are simply absent from the ledger — an omission, not a declared deferral. `PRIVATE_REASONING_REQUESTED` in particular has no corresponding field in the pack format at all, so nothing could reject it. |

## Per-line mapping against #9's thirteen deterministic admission controls

The "5 of 7 mechanized" figure elsewhere in this repository counts against the
noodles pack's own seven-item DRIFT ledger, not against #9's own control list.
Against #9's thirteen, as of the paired `ed3c/skill-concerns#10` STAGE-P0 atom
landing alongside this one (row 7's `--head`/stale-projection mechanism is
`#10`'s addition, absent from this admission taken alone):

| # | #9's control | Status |
|---|---|---|
| 1 | denominator source accounted for or `ABSENT`/`BLOCKED` | Mechanized (`SOURCE_UNDECLARED`, `DENOMINATOR_SHRINK`, `DENOMINATOR_ABSENT`) |
| 2 | every statement has a source anchor and classification | Mechanized (`SECTION_UNANCHORED`) — at section, not per-statement, granularity |
| 3 | N/P cannot be labeled L/R or cited as completion evidence | Mechanized (`EVIDENCE_PROMOTION`) on the authority field only; see `classification_vs_authority_note` in the L1 topology for why the similarly-named classification tokens `L_REFERENCE`/`R_REFERENCE` are a different axis and do not trigger it |
| 4 | start-readiness cannot satisfy completion edge | Mechanized (`EDGE_CLASS_COLLAPSE`) |
| 5 | every convergence has exactly one owner | Mechanized (`DUPLICATE_WRITER`, `UNOWNED_CONVERGENCE`) |
| 6 | every molecular leaf has backward+forward link or explicit gap | Partial: `TRACEABILITY_GAP_RULE_ABSENT` proves the vocabulary word is present somewhere in the file; it does not walk every lane row to confirm each one individually names a link or a gap |
| 7 | stale Issue/PR/head/body snapshots detected | Partial: snapshot-id/baseline-commit self-consistency and `--head` freshness are mechanized; Issue/PR/body staleness specifically needs the provider readback PN-7 declares `NOT_MECHANIZED` |
| 8 | duplicate durable owner/writer detected | Mechanized (`DUPLICATE_WRITER`) |
| 9 | source omission and denominator shrink fail | Mechanized (`SOURCE_UNDECLARED`, `DENOMINATOR_SHRINK`) |
| 10 | external claim stays `EXTERNAL_CLAIM` without a primary-source receipt | Not mechanized as a dedicated check; `EVIDENCE_PROMOTION` would catch an authority elevation, but nothing specifically pins an `EXTERNAL_CLAIM`-classified statement to staying unpromoted as a distinct rule |
| 11 | pack cannot create/close/merge/modify an Issue in the hermetic consumer | Declared, not mechanized: `LAW-NO-MUTATION`'s topology row states directly that the checker holds no provider credential, so this is true by construction rather than by an assertion that could go red |
| 12 | private-chain-of-thought fields are rejected | **Not mechanized, not declared.** No code, ledger row, or `NOT_MECHANIZED` entry exists for this control; the pack format has no chain-of-thought field concept for a rejection to apply to |
| 13 | unavailable consumer APIs stay `BLOCKED`/`NOT_EXERCISED`, never `VERIFIED` | Mechanized (`consumer_canary` state check plus the `consumer-canary-overclaimed` admission control) |

Row 12 is the one outright gap: not a documented deferral like PN-5/PN-7, just
an absent control. Rows 6, 7, and 10 are real but partial. This table is the
per-line mapping the "5 of 7" framing does not provide on its own.

## Non-claims

This bundle does not replace the Shadow Architect, Tech Lead, or
procedural-runtime methods, or the already-admitted local bundles it may compose
with. It does not make a long context complete because six files exist, does not
guarantee an Agent reads or obeys the context, does not create a second
specification, registry, closure database, scheduler, worktree manager, or merge
authority, and does not treat conversation, article, PDF, or model consensus as
verified truth.
