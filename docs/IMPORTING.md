# Importing and refactoring a Skill

## Source repository contract

For a Git source, record:

```json
{
  "source_kind": "git",
  "repository": "https://github.com/owner/repo",
  "commit": "<40 hex>",
  "source_path": "skills/example",
  "locked_files": [
    {"path": "skills/example/SKILL.md", "sha256": "..."}
  ]
}
```

Use a local checkout already bound to the exact commit; this repository does not infer a commit from a branch name.

A helper can create a lock from a local checkout:

```bash
python3 scripts/freeze_source.py \
  --checkout /absolute/path/to/source \
  --repository https://github.com/owner/repo \
  --commit <40-hex> \
  --source-path skills/example \
  --output intake/example/source-lock.json
```

## Refactor rules

1. Preserve load-bearing old strengths as named assertions or explicit retained non-claims.
2. Keep the upstream source bytes immutable.
3. Classify the new bundle as `procedure-rich`, `domain-rich`, or `composed`.
4. Put portable method in `SKILL.md`.
5. Put source/product-specific knowledge only in declared domain paths.
6. Put execution in scripts and tests.
7. Add positive and planted negative controls.
8. Bind a complete source lock and complete Skill-tree admission receipt.
9. State the exact evidence ceiling.
10. Treat consumer, live-runtime, and production proof as separate future layers.

## `skills-shared` boundary

`skills-shared` may remain the upstream instruction/method and incubation repository. A migration into `skill-concerns` is a content-bound refactor, not a symlink or passive mirror.

The initial repository method reference is frozen to:

```text
ed3c/skills-shared
commit 52b29b38ded9eaacbf7fb1bfa8ccf69ab37870b9
path   skills/skill-refactor-proof-loop
```

Only its small reusable laws are adopted here: source freeze, old-strength preservation, route reachability, negative controls, denominator completeness, and evidence-layer monotonicity. Its repository-specific issue/PR topology, provider state, and live receipts are not imported.
