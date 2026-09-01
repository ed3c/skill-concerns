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
| `scripts/admission_stamp.py` | the one stamp surface: re-runs a Skill's `run_all.SKILL_CHECKS` row and refuses to write a receipt when any of it is red |
| `policy/bootstrap-admissions.json` | the trusted first-admission allowlist: which Skill's first-ever admission is authorized, the exact skill-tree digest it authorizes, and the check argv to execute against it — both fields are resolved by `admission_stamp.bootstrap_checks`, and an entry carries nothing else |
| `admissions/<skill>.json` | complete content-bound admission subject and ceiling |
| `policy/upstream-pins.json` | the upstream facts this repository's method rests on: the canonical pstack commit, the requirement that it stay reachable from that repository's branch, and the files to re-read when the branch moves |
| GitHub Actions run | execution arrival for one checked-out commit |

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

**BUILD** is `python3 scripts/maintain_skills.py --pass <skill>` and may only PROPOSE: it creates `maintain/<skill>-<stamp>`, regenerates corrections through the subject Skill's own `scripts/gen_*.py` producers (never by hand — spatial-loop-grounded C5), commits them there, and returns the checkout to the base branch with its head sha re-read and asserted unchanged. Writes may land only under `skills/<skill>/` within this checkout; the guard is `git status --porcelain -uall` after every producer, so one out-of-scope path *inside this working tree* refuses the whole producer, restores the tree, and blocks the pass — a producer that writes to an absolute path outside this checkout entirely is outside what a git-status diff can see, and nothing today checks that `root` is exclusively owned by this pass for its duration either (filed: ed3c/skill-concerns#66, not fixed here). Producers whose output is a repository artifact by contract (`gen_admission.py` → `admissions/`, `gen_source_lock.py` → `intake/`) are excluded rather than refused every run.

Corrections are **proven** before they become a commit: the subject's own `run_all.SKILL_CHECKS` row runs against the proposal, and a red row blocks the pass (`BUILD_PROPOSAL_UNPROVEN`) instead of shipping regenerated bytes nobody re-ran. A skill with no row in `SKILL_CHECKS` at all is blocked the same way (`BUILD_SKILL_UNCHECKED`) rather than reading as vacuously proven — absence and a green row must not carry the same report shape. That row and no more — `check_admissions.py` reds by construction on any BUILD proposal, because the admission receipt pins the bytes BUILD just moved and the re-stamp writes `admissions/`, outside BUILD's edit scope on purpose. **Re-stamping belongs to the landing ceremony, not to a pass that may only propose**, so a BUILD branch is an input to the change procedure below, never a substitute for it.

Planted negatives keep all of this falsifiable in `--selftest`: a repository gate that writes into `skills/` (SHADOW), a producer that writes into `policy/` (BUILD scope), a producer whose output reds the subject's own row (BUILD proof), and a proposal for a skill with no `SKILL_CHECKS` row at all (BUILD proof, absence case).

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
