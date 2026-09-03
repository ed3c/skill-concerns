# AGENTS.md — `skill-concerns` operating contract

<!-- agent-next: skills/AGENTS.md -->

`skill-concerns` is the **Admitted Skill Distribution Plane**. Its `main` branch may contain only Skill bundles whose source identity, concern boundaries, executable routes, negative controls, and evidence ceiling are physically checked.

This repository does not own source-repository incubation, consumer worktrees, product credentials, provider sessions, live UI state, or production receipts.

## Three-document Agent route

The complete `AGENTS.md` route is:

```text
1. /AGENTS.md
2. /skills/AGENTS.md
3. /skills/<skill>/AGENTS.md
```

Three documents is the hard ceiling, including the root document. No `AGENTS.md` may exist below a Skill root. [`agents-routing.json`](agents-routing.json) is the machine route; `scripts/check_agents_hops.py` rejects missing nodes, drift, cycles, unreachable documents, and a fourth document.

After the third `AGENTS.md`, read only the target Skill's `README.md`, `SKILL.md`, manifest, selected references, executable mechanisms, eval cases, and exact issue/PR subject. Do not recursively load unrelated Skills.

## Golden Path

```text
SOURCE_SELECTED
→ SOURCE_FROZEN
→ CONCERNS_EXTRACTED
→ CANDIDATE_REFACTORED
→ STRUCTURE_VERIFIED
→ EXECUTABLE_ROUTES_VERIFIED
→ HERMETIC_EVAL_VERIFIED
→ DENOMINATOR_RECONCILED
→ ADMISSION_RECEIPT_BOUND
→ HOSTED_EXACT_HEAD_CHECKED
→ MAIN_PROMOTION_ELIGIBLE
```

A missing transition is a stop, not an invitation to fill the gap with prose.

### Probabilistic work

Agents may propose:

- actor-visible feature boundaries;
- procedure/domain/execution separation;
- refactor structure;
- domain adapters;
- risk-based journey reduction;
- candidate assertions;
- exploration of unknown repositories.

These outputs remain proposals until a deterministic gate consumes exact bytes.

### Physically enforced work

Scripts and tests must establish:

- immutable source and candidate file identities;
- the three-document Agent route;
- required Skill anatomy;
- portable-core versus domain-path separation;
- entrypoint-to-checker-to-test reachability;
- positive, hollow, and mutation controls;
- every changed feature has a proof journey;
- every reachable terminal has an observable oracle or an explicit blocked record;
- `VERIFIED` is backed by production-equivalent observable evidence;
- every skip names a blocker, nearest reachable path, and residual uncertainty;
- the admission receipt covers the complete Skill tree and selected shared contracts;
- higher evidence layers remain explicit and cannot be promoted by wording.

## Dual-standard conformance

A new Skill's shape used to split in half: one half already mechanical, the
other half author memory that an admission issue could enumerate and nothing
would re-read. `scripts/check_skill_bundles.py` now sweeps every `skills/*`
directory and refuses the second half too (ed3c/skill-concerns#74):

- a validator exists, is **wired** into its own `run_all.SKILL_CHECKS` row
  alongside that Skill's test discovery, and is **count-tied** to its entrypoint
  through the `SKILL_MD_CLAUSES` tuple it declares in its own bytes — a hollowed
  `SKILL.md` reds against a tuple the hollowing never touched;
- an admission stamp exists and was taken against the bytes that are here now;
- the eval campaign is a directory, and no planted-negative arm shares its
  producing assertion with a positive one;
- every `receipts.json` entry names its ground — a `producer` path that exists,
  provider/host `refs`, or the explicit `HOST_OBSERVED` exit for a one-time host
  observation nothing here replays. That exit is not free
  (ed3c/skill-concerns#91): the entry must also name an `observer` — what
  actually made the observation — and a `carried` path inside its own bundle
  whose bytes cite that receipt key. The citation is the obligation; a pointer
  at any file that merely exists would be the same vacuity one level down;
- both collection documents carry the Skill's row, kind included;
- the pstack birth triple is present by shape: feature map, refusing Doctor,
  prove-once receipt.

The gate reads bytes and never imports a candidate module: the count tie comes
from each Skill's own validator, so there is no per-skill list here to go stale.
What it cannot prove is method honesty — that the interview behind a feature map
was faithful, that a campaign arm measured anything. That stays with campaigns,
planted negatives, and wave monitors, and this sweep does not pretend otherwise.

Each assertion has its own planted negative in
`tests/test_repository_controls.py`; a clean sweep alone never shows a sweep can
red.

## Concern ownership

```text
SKILL.md
  portable decision policy and stop laws

references/
  reusable semantic contracts, schemas, and examples

domain adapter
  repository/product commands, selectors, flags, fixtures, and environment bindings

scripts/ + tests/
  execution, observation, assertions, negative controls, and deterministic receipts

feature map
  actor-visible capability, states, transitions, variants, and observable contract

admission receipt
  content identity and measured evidence ceiling; never an execution engine
```

A generic Skill must not absorb a product's selectors, command names, repository paths, account state, or runtime bindings. A domain-rich Skill may contain them only in declared domain paths and must carry matching physical verification.

## Evidence layers

```text
L0_SOURCE_FREEZE
L1_STRUCTURAL
L2_EXECUTABLE_CONTRACT
L3_HERMETIC
L4_MATCHED_LIVE_RUNTIME
L5_DELIVERY_AND_PRODUCTION
```

`ADMITTED` means the repository's configured minimum layer was physically reached for the exact content-bound subject. It does not mean every higher layer passed.

Use these states:

```text
PASS
FAIL
ABSENT
BLOCKED
NOT_EXERCISED
HUMAN_ADMIT_REQUIRED
```

A passing unit test cannot become live-runtime proof. A GitHub check cannot become product-behavior proof. A skipped path is never a pass.

This ladder is about **what one commit proved**. It is not a bundle's `L0 procedural / L1 domain / L2 execution` concern layers, which are about **where bytes belong**, and it is not the arrival ledger's `DECLARED / EXERCISED / PRODUCTION`, which is about **who reached a capability**. Arrival is spelled in words rather than numbers so that two L-numberings exist here rather than three; `skills/arrival-engineering` owns the arrival vocabulary and no other document may redefine it.

## Authority files

| Authority | Owns |
|---|---|
| `agents-routing.json` | complete `AGENTS.md` graph and depth ceiling |
| `registry.json` | admitted inventory, Skill kind, minimum evidence, receipt path |
| `contracts/*.schema.json` | machine contract shapes |
| `skills/<skill>/skill.json` | one bundle's concern split and executable routes |
| `skills/<skill>/SKILL.md` | portable Agent method |
| `skills/<skill>/references/` | reusable semantics |
| `skills/<skill>/scripts/` | deterministic mechanisms |
| `skills/<skill>/tests/` and `evals/` | positive and negative falsifiers |
| `intake/<skill>/source-lock.json` | frozen source/proposal identity |
| `scripts/run_all.py` | `SKILL_CHECKS`: the single declaration of each Skill's check argv, and the suite that runs it |
| `scripts/check_skill_bundles.py` | the repository-wide dual-standard conformance sweep: bundle anatomy plus validator wiring, count tie, stamp freshness, campaign arms, receipt grounds, collection rows, and birth artifacts |
| `scripts/admission_stamp.py` | the one stamp surface: re-runs a Skill's `run_all.SKILL_CHECKS` row and refuses to write a receipt when any of it is red |
| `policy/bootstrap-admissions.json` | the trusted first-admission allowlist: which Skill's first-ever admission is authorized, the exact skill-tree digest it authorizes, and the check argv to execute against it — both fields are resolved by `admission_stamp.bootstrap_checks`, and an entry carries nothing else |
| `admissions/<skill>.json` | complete content-bound admission subject and ceiling, plus `graded_by`: the argv that graded this receipt, emitted from the same `admission_stamp.declared_checks()` selection the grading executes, so a bundle graded through its permanent `SKILL_CHECKS` row and one graded through a bootstrap entry no longer produce identical receipts (ed3c/skill-concerns#133) |
| `policy/upstream-pins.json` | the upstream facts this repository's method rests on: the canonical pstack commit, the requirement that it stay reachable from that repository's branch, and the files to re-read when the branch moves. A pin may instead watch FILE identity alone, with no `pinned_commit`, when the upstream head moves routinely and only the bytes matter — the consumer issue-admission gate a Skill mirrors is pinned that way (ed3c/skill-concerns#97), and a watched file may name the local `mirror` its drift is filed against |
| `skills/arrival-engineering/domain/capability-topology.json` | the arrival ledger: every declared capability, the exit it is bound to, and the highest arrival level its receipts support. Rows without a resolvable receipt are refused at append |
| GitHub Actions run | execution arrival for the trees `verify.yml` checks out: the candidate head, and the merge result `refs/pull/<n>/merge` that would become `main` (ed3c/skill-concerns#111) |

Markdown may explain these files but cannot override them.

## Mandatory stop laws

Stop with `FAIL`, `ABSENT`, or `BLOCKED` when:

- source bytes or provenance are missing;
- a candidate silently replaces its source treatment;
- an `AGENTS.md` route exceeds three documents or cycles;
- a declared route does not reach its executable checker and tests;
- a procedure-rich portable core contains a declared forbidden domain literal;
- a changed feature has no journey;
- a reachable terminal has neither oracle nor explicit blocked record;
- a `VERIFIED` journey has only static, unit, mock, or internal evidence;
- a skip omits blocker, nearest reachable path, or residual uncertainty;
- a receipt omits a Skill file or hashes stale bytes;
- failed or blocked controls are removed from the denominator;
- the claimed evidence layer exceeds the executed layer;
- cleanup or exact-subject identity is unknown.

## Content freshness (N-class)

Admission proves a Skill's content at one commit. It says nothing about the day after: receipts pin paths, digests, provider refs, and upstream commits that keep moving while nothing re-reads them. `scripts/maintain_skills.py` is the cadence owner for that decay — daily under `ops/com.neon.maintain-skills.plist`, and by hand with `python3 scripts/maintain_skills.py`.

The sweep re-runs each Skill's own `run_all.SKILL_CHECKS` row and the three repository gates, then re-checks the pins no gate can see: every receipt ref must still resolve at the provider, and `policy/upstream-pins.json` must still hold. It reports one of three outcomes — `clean`, `changed` (drift found), `blocked` (coverage unfinished) — and never patches what it finds: each drift leaves as a finding with a `path:line` destination in this tree. A ref that names a host artifact is reported unreachable with its prerequisite, never as a pass.

The sweep is **N-class: it gates nothing.** No admission, stamp, or CI path reads its exit code or its report, and `tests/test_maintain_skills.py::test_sweep_gates_nothing` reds if one ever starts. Its own falsifier is `python3 scripts/maintain_skills.py --selftest`: planted drift must be detected, filed with a destination, and left unfixed.

### The BUILD/SHADOW split

The maintain loop has two halves and only one of them may write. **SHADOW** is the default pass and has no write verb at all; it proves it stayed a reader by digesting the edit scope before and after, and a pass whose digest moved refuses its own report (`EDIT_SCOPE_VIOLATION`, `blocked`) rather than publishing findings read off a tree something mutated underneath it.

**BUILD** is `python3 scripts/maintain_skills.py --pass <skill>` and may only PROPOSE, inside a **linked worktree** it creates and deletes — never in the checkout it was handed (ed3c/skill-concerns#66). `git worktree add <tmp> -b maintain/<skill>-<stamp>` opens a disposable tree; producers, proof and the commit all run there, and the commit reaches `maintain/<skill>-<stamp>` in this repository because the object store is shared. Corrections regenerate through the subject Skill's own `scripts/gen_*.py` producers (never by hand — spatial-loop-grounded C5). Producers whose output is a repository artifact by contract (`gen_admission.py` → `admissions/`, `gen_source_lock.py` → `intake/`) are excluded rather than refused every run.

Three properties, and what each one does and does not cover:

- **Root exclusivity.** `git checkout -b` in the caller's own tree is what the worktree replaces: it moved the HEAD of whatever checkout it was handed, and a refusal's restore step could delete files a concurrent session wrote after the dirty check ran. Neither is reachable now, so the caller's tree no longer has to be clean for a pass to start; instead its HEAD and `git status --porcelain -uall` are read **before and after**, and any movement is `BUILD_CALLER_TREE_MUTATED`. Measured, not assumed.
- **Containment.** Writes may land only under `skills/<skill>/` inside the worktree; the guard is `git status --porcelain -uall` after every producer, so one out-of-scope path refuses the whole producer and blocks the pass, and the worktree is *deleted* rather than restored. A producer that writes to an absolute path outside the worktree entirely is still outside what a git-status diff can see. #66 confines the blast radius to a disposable directory and does not claim to close that; the pass says so in its own report (`caller.unseen`) rather than only here.
- **Proposal lifecycle.** A `changed` outcome leaves ONE branch and nothing else — the worktree is removed on every outcome, and `clean` and `blocked` take the branch with it. A second pass for the same skill is refused with `DOCTOR_PROPOSAL_OUTSTANDING` naming the branch, so proposals cannot accumulate and the human who asked for one owns it until they land it or `git branch -D` it. Pruning stale branches automatically was the other candidate and is worse: it deletes unpushed commits a human may still intend to land.

Corrections are **proven** before they become a commit: the subject's own `run_all.SKILL_CHECKS` row runs against the proposal, and a red row blocks the pass (`BUILD_PROPOSAL_UNPROVEN`) instead of shipping regenerated bytes nobody re-ran. A skill with no row in `SKILL_CHECKS` at all is blocked the same way (`BUILD_SKILL_UNCHECKED`) rather than reading as vacuously proven — absence and a green row must not carry the same report shape. That row and no more — `check_admissions.py` reds by construction on any BUILD proposal, because the admission receipt pins the bytes BUILD just moved and the re-stamp writes `admissions/`, outside BUILD's edit scope on purpose. **Re-stamping belongs to the landing ceremony, not to a pass that may only propose**, so a BUILD branch is an input to the change procedure below, never a substitute for it.

Planted negatives keep all of this falsifiable in `--selftest`: a repository gate that writes into `skills/` (SHADOW), a producer that writes into `policy/` (BUILD scope — and its bytes now land in the disposable worktree, so the arm measures containment rather than a restore), a producer whose output reds the subject's own row (BUILD proof), a proposal for a skill with no `SKILL_CHECKS` row at all (BUILD proof, absence case), and a second pass launched while a proposal is outstanding (lifecycle), with the human's discharge of that obligation — `git branch -D` — asserted to clear the refusal.

### BUILD may only carry adjudicated cures (ed3c/skill-concerns#93)

A BUILD proposal that introduces or alters an **enforcement shape** — a gate, a
ratchet, a threshold, a refusal, an escape-hatch condition — must name its
**cure-authorization**: an issue whose body carries the discriminating
measurement or the falsification, or an operator adjudication that **resolves**.
A proposal without one is refused with `BUILD_CURE_UNAUTHORIZED`
naming this rule, and a SHADOW detection never authorizes — detection is the
beginning of an adjudication, not a license to cure.

An operator adjudication resolves rather than parses (ed3c/skill-concerns#103).
The form used to be any date plus any non-empty text, which the wave-19 judge
falsified by running three garbage refs through the committed catalogue on
landed main — all three passed, `operator:2026-09-01:the vibes were good`
included. It must now name a **pinned subject** that exists in the tree and that
its own ref repeats, and carry **either** an issue reference whose body holds the
adjudication — a provider ref the cadence sweep re-resolves — **or** an inline
adjudication record with an expiry or a re-resolution cadence. A lapsed inline
record is refused *as expired*, which is a different state from malformed, and
every carrier passes the tree the subject resolves against rather than falling
back to a weaker shape-only reading. What is still not judged is the QUALITY of
the adjudication the artifact carries; that residue is registered with a sensor
and a trigger in `skills/red-team/domain/residual-sensor-register.json`.

The trigger was a lane that copied the nearest successful enforcement precedent
(a report-only metric plus a monotonic ratchet) into a new debt issue; the
successor atom then measured three candidates and proved the copied shape wrong,
because a blanket growth bound misjudges every normal test addition as
architectural regression. Cure-shape selection therefore needs a discriminating
measurement *before* the shape is picked, and a write verb that auto-proposes
cures for detected patterns automates exactly that error.

This repository owns four BUILD carriers — `scripts/maintain_skills.py --pass`,
`skills/arrival-engineering`'s topology append, `skills/red-team`'s catalogue
fold-in, and `skills/shadow-architect`'s precedent fold-in — and they call
**one** implementation,
[`scripts/cure_authorization.py`](scripts/cure_authorization.py), rather than
each reading the rule. The first two scan the proposal for the five shape
words; the last two pass `always=True`, because a catalogue class and a
precedent clause each ARE an enforcement shape and re-deriving that from their
wording would prove nothing.
`tests/test_repository_controls.py::CureAuthorizationTests` is the mechanical
reader for the single-implementation claim and for these bytes. Detection is
fail-closed: the five shape words are matched on word boundaries over a
proposal's added lines, so a false positive costs one named authorization while
a false negative would ship an unadjudicated shape.

Out of scope with receipts: `dynamic-workflow` is observer-only and cannot write
inside its subject; pstack stays the pinned canonical, so this rule binds at the
consumer layer and never by forking the ceremony; the noodles daemon's execute
path only implements adjudicated issues, so every cure it carries already
arrives with an issue as its authorization. The rule binds from landing forward
— no retroactive audit of past proposals.

### Adjudications carried here as bytes (ed3c/skill-concerns#59)

- **Runtime/ceremony boundary.** A supervising reader owns RUNTIME liveness of the sessions it watches — session write age, spawn surface, death signatures, falsely-dead versus dead shapes. CEREMONY correctness — receipt verbatim discipline, marker-transition legality, handoff — stays with the Skill that owns that ceremony. Same lane, two lenses. Entries covering another Skill's ceremony must POINT at it, never restate it; a restated copy is the drift the split exists to prevent.
- **Filing-not-reflex coupling.** An observation-time finding never auto-invokes a maintain pass. Findings are mechanically FILED at a strict destination with a named owner, and the daily cadence consumes them on its own schedule — admitted means auto-enrolled. An auto-maintain path would let a reader rewrite its own lens until a finding disappears: self-laundering, the exact write path the reader-only contract forbids. Most observation findings concern the OBSERVED system anyway and are out of maintain's edit scope by its own contract; only lens-drift findings are maintain territory.
- **Trigger-not-apply exception.** When a driver's own selftest goes red mid-observation — the lens is provably broken now — the observation report auto-degrades itself to lens-suspect and one immediate maintain pass is SCHEDULED. That pass still lands through the full PR and gate ceremony, never an inline edit. Trigger automation is admitted because it keeps every gate; application automation is not.

### First-ever admission (ed3c/skill-concerns#72)

The checks that grade a candidate are declared on the trusted side, so a candidate cannot vouch for itself — and so a Skill's *first* admission cannot happen at all: the commit that adds the Skill is the commit that adds its `SKILL_CHECKS` row, and the gate reads that row from a branch that commit is not on yet.

A first admission is therefore **two landings, in this order**:

1. A reviewed atom lands one entry in `policy/bootstrap-admissions.json` naming the incoming Skill, the sha256 of the exact skill tree it authorizes, and the check argv to run. `main` is green with the entry present and the Skill directory still absent; nothing executes until a tree with those exact bytes arrives. An entry carries no field that nothing resolves — the reviewed head and the issue it came from are the landing commit's to record, and `git log` is what reads them back.
2. The Skill's own PR lands the bundle, its permanent `SKILL_CHECKS` row, and **the deletion of its bootstrap entry** in the same commit.

The entry is spent by step 2, not merely superseded by it: `check_admissions.py` reds with `BOOTSTRAP_ENTRY_STALE` on any entry whose Skill directory exists in the same tree, so an authorization cannot outlive the admission it was written for. It never widens anything else — a Skill that already owns a `SKILL_CHECKS` row is graded by that row and never reads the allowlist, bytes that differ from the authorized digest are refused before they execute, and no entry falls through to the same `NO_DECLARED_CHECKS` refusal an unknown Skill has always had.

## Change procedure

1. Bind one issue and one branch. A Skill arriving for the first time binds two, per the ceremony above.
2. Freeze the source proposal or Git source before refactoring.
3. Keep portable procedure, domain knowledge, execution mechanics, and proof artifacts in separate declared paths.
4. Add positive and planted negative controls before admission.
5. Run `python3 scripts/run_all.py`.
6. Once the candidate bytes are final, stamp the receipt with that Skill's `scripts/gen_admission.py`. Sequencing is not carried here: the stamper re-runs the Skill's own validator and test discovery and refuses to write while any of them is red.
7. Run the complete suite again.
8. Publish a PR whose body names the exact evidence ceiling and all unexercised higher layers.
9. Merge only the exact checked head that passed required repository gates.

## Completion packet

Report:

```text
source lock and exact upstream identity
changed Skill paths and kind
three-document route result
portable/domain/execution concern split
positive and negative controls executed
complete Skill-tree and shared-contract digest
highest physically reached evidence layer
hosted exact-head status
all higher NOT_EXERCISED / BLOCKED / HUMAN_ADMIT_REQUIRED lanes
issue, branch, PR base/head, and rollback subject
```

Never claim matched live-model uplift, consumer integration, production behavior, merge, or release without exact evidence for that separate layer.
