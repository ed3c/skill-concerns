from __future__ import annotations

import sys
import unittest
from pathlib import Path

# The skill directory name is hyphenated, so a package import can never
# resolve; load the validator by path like every other admitted skill's tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_rendered_contract import validate  # noqa: E402


GOOD = """
## Context Model
The locally obvious change should be the globally correct change.
## Core Architecture Rules
Use one obvious writer and prefer an isolated extension.
## Enforcement Hierarchy
Use the strongest practical enforcement layer. Repeated human correction is evidence of a missing system constraint.
## Shortest Path Should Be the Best Path
Make local imitation safe.
## Greenfield Systems
Seed a golden path.
## Human Slop and Agent Slop
Move repeated failures into mechanisms.
## Rewrite Safety
Use an executable migration contract.
## Adding New Architecture
A new layer that makes every future Agent understand more concepts is presumptively suspect.
## Implementation Procedure
Choose the smallest architecture-preserving path.
## Best Path Decision Rule
Do not choose the shortest path merely because it compiles.
"""


class RenderedContractTests(unittest.TestCase):
    def test_accepts_self_contained_contract(self) -> None:
        self.assertEqual(validate(GOOD), [])

    def test_rejects_black_box_source_vocabulary(self) -> None:
        errors = validate(GOOD + "\nUse the Noodle-owned worktree and FeatureMap.\n")
        self.assertTrue(any("black-box" in error for error in errors))

    def test_rejects_evidence_machinery_in_hot_path(self) -> None:
        errors = validate(GOOD + "\n## Evidence lookup\nResolve claim_id in evidence-manifest.json.\n")
        self.assertTrue(any("evidence/compiler machinery" in error or "black-box" in error for error in errors))

    def test_rejects_semantic_loss(self) -> None:
        hollow = GOOD.replace("Do not choose the shortest path merely because it compiles.", "Choose a short path.")
        errors = validate(hollow)
        self.assertTrue(any("load-bearing Best Path semantic missing" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
