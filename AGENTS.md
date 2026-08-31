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
| `scripts/admission_stamp.py` | the one stamp surface: each Skill's check table, and the refusal that keeps an unmeasured `PASS` out of a receipt |
| `admissions/<skill>.json` | complete content-bound admission subject and ceiling |
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

## Change procedure

1. Bind one issue and one branch.
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
