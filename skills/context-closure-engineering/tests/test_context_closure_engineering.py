"""Eval harness for context-closure-engineering: positive controls + hollow mutations.

Every mutation models a way this bundle could silently degrade while the suite
stayed green; each must FAIL the validator. This is the hillclimb gate.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_context_closure_engineering import validate  # noqa: E402


def mutated_copy() -> tuple[tempfile.TemporaryDirectory, Path]:
    temp = tempfile.TemporaryDirectory(prefix="cce-eval-")
    root = Path(temp.name) / "skill"
    shutil.copytree(SKILL_ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
    return temp, root


def topology(root: Path) -> tuple[Path, dict]:
    path = root / "domain" / "context-closure-topology.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


class ContextClosureEngineeringEvals(unittest.TestCase):
    def test_positive_control_passes(self) -> None:
        self.assertEqual(validate(SKILL_ROOT), [])

    def test_context_pack_selftest_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "check_context_pack.py"),
             "--selftest"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_layer_file_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        (root / "references" / "portable-context-closure-policy.md").unlink()
        self.assertTrue(
            any("L-layer" in error or "L0" in error for error in validate(root)),
            validate(root),
        )

    def test_law_clause_dropped_fails(self) -> None:
        # Deleting one L0 clause while the L1 ledger still declares eight must
        # break the count tie, not merely shrink the document.
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "references" / "portable-context-closure-policy.md"
        text = path.read_text(encoding="utf-8")
        head, _, _ = text.partition("## LAW-EXTERNAL-CLAIM")
        path.write_text(head, encoding="utf-8")
        errors = validate(root)
        self.assertTrue(any("LAW-EXTERNAL-CLAIM" in error for error in errors), errors)

    def test_negative_demoted_without_owner_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path, document = topology(root)
        for negative in document["planted_negatives"]:
            if negative["state"] == "MECHANIZED":
                negative["state"] = "NOT_MECHANIZED"
                negative.pop("checks", None)
                break
        path.write_text(json.dumps(document, indent=2), encoding="utf-8")
        errors = validate(root)
        self.assertTrue(any("NOT_MECHANIZED without" in error for error in errors), errors)

    def test_negative_count_drift_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path, document = topology(root)
        document["planted_negatives"].pop()
        path.write_text(json.dumps(document, indent=2), encoding="utf-8")
        errors = validate(root)
        self.assertTrue(any("planted_negative_count" in error for error in errors), errors)

    def test_consumer_canary_overclaim_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path, document = topology(root)
        document["consumer_canary"]["state"] = "VERIFIED"
        path.write_text(json.dumps(document, indent=2), encoding="utf-8")
        errors = validate(root)
        self.assertTrue(any("consumer_canary" in error for error in errors), errors)

    def test_checker_assertion_defused_fails(self) -> None:
        # Weakening the edge-class comparison defuses PN-2; the selftest, and so
        # the gate, must go red rather than reporting a smaller contract green.
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "scripts" / "check_context_pack.py"
        text = path.read_text(encoding="utf-8")
        defused = text.replace(
            "if match and match.group(1) not in permitted:",
            "if match and False:",
        )
        self.assertNotEqual(defused, text, "mutation target drifted")
        path.write_text(defused, encoding="utf-8")
        errors = validate(root)
        self.assertTrue(any("selftest" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
