# Exploration policy

## Preserve unknowns

Do not convert guesses into constraints. Keep selector, command, endpoint, component, provider, and architecture questions open until repository or runtime evidence resolves them.

## Promote only stable knowledge

Promote knowledge into a feature map or adapter when it is:

- actor-visible;
- repeatedly relevant;
- needed to verify behavior;
- a stable entry point or environment boundary;
- required to prevent a demonstrated failure mode.

Keep incidental implementation facts discoverable.

## Runtime conflict

When runtime behavior contradicts the map:

1. bind the exact revision and environment;
2. reproduce through a supported path;
3. decide whether the implementation or map is wrong;
4. repair the wrong subject;
5. retain the contradiction as evidence until reconciled.

Do not force implementation to satisfy stale prose without checking intended behavior.
