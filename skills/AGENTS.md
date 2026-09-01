# AGENTS.md — admitted Skill collection contract

<!-- agent-next: skills/feature-map-engineering/AGENTS.md, skills/control-noodle/AGENTS.md, skills/spatial-loop-grounded/AGENTS.md, skills/control-code-intel/AGENTS.md, skills/control-backup/AGENTS.md, skills/context-closure-engineering/AGENTS.md, skills/dynamic-workflow/AGENTS.md -->

This is the second of exactly three Agent documents.

## Read rule

1. The root `AGENTS.md` is already authoritative.
2. Read this collection contract.
3. Read only the target Skill's root `AGENTS.md`.
4. Stop loading `AGENTS.md` files. The target Skill may then route to its own `README.md`, `SKILL.md`, manifest, selected references, scripts, tests, and eval inventory.

No `AGENTS.md` may exist below a Skill root.

## Collection invariant

Every directory immediately below `skills/` is an admitted bundle listed in `registry.json`. A bundle is complete only when:

- its name, path, and kind agree across registry, manifest, directory, and `SKILL.md`;
- its declared portable, domain, execution, test, and eval paths exist;
- a deterministic route reaches the implementation and planted negative controls;
- a source lock and content-bound admission receipt cover the exact bytes;
- the evidence ceiling meets repository policy;
- every higher layer remains explicit.

Do not add examples, drafts, or partial migrations under `skills/`. Keep a candidate on its issue branch until the complete admission suite is green.
