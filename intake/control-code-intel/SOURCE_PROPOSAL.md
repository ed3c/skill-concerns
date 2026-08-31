# Source proposal — control-code-intel

Promote the physically-verified code-intelligence control method into an
admitted, eval-gated domain-rich skill.

Grounding environment: the 2026-08-31 code-intel wiring + cross-repo session on
ed3c/noodles and ed3c/skill-concerns. The code-intel v1 stack converged in
ed3c/noodles#13 from the landed band (#5 SQLite, #6 tree-sitter, #7 grepai,
#8 Serena nav, #10 SCIP, #9 canary, #12 Serena edit); LanceDB was dropped on a
measured loss (#11 / PR #231). This session then wired the interactive layer:
grepai + Serena MCP servers, pgvector 0.8.0 built from source for
postgresql@16, and a cross-repo grepai workspace over noodles + skill-concerns
whose repo-distinctive queries returned the correct repository.

Three layers, one method (repo ARCHITECTURE L0/L1/L2): L0 portable policy,
L1 domain topology, L2 executable driver + assertions. Every admitted tool
carries a physical receipt; the L2 driver replays their assertions with
negative controls. Promotion rule: a tool enters only on measured advantage;
the eval suite may only be extended, never weakened.
