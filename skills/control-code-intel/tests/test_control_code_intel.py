"""Eval harness for control-code-intel: positive controls + hollow mutations.

Every mutation models a way the three-layer skill could silently degrade; each
must FAIL the validator (or the L2 driver selftest). This is the hillclimb gate.
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

from validate_control_code_intel import validate  # noqa: E402


def mutated_copy() -> tuple[tempfile.TemporaryDirectory, Path]:
    temp = tempfile.TemporaryDirectory(prefix="cci-eval-")
    root = Path(temp.name) / "skill"
    shutil.copytree(SKILL_ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
    return temp, root


class ControlCodeIntelEvals(unittest.TestCase):
    def test_positive_control_passes(self) -> None:
        self.assertEqual(validate(SKILL_ROOT), [])

    def test_l2_driver_selftest_passes(self) -> None:
        r = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "code_intel_driver.py"), "--selftest"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_layer_file_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        (root / "references" / "portable-code-intel-policy.md").unlink()
        self.assertTrue(any("L-layer" in e or "L0" in e for e in validate(root)), validate(root))

    def test_unbacked_receipt_removed_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        p = root / "receipts.json"
        d = json.loads(p.read_text())
        d["evidence"].pop("cross-repo-verified")
        p.write_text(json.dumps(d))
        self.assertTrue(any("cross-repo-verified" in e for e in validate(root)), validate(root))

    def test_lancedb_admitted_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        p = root / "domain" / "code-intel-topology.json"
        d = json.loads(p.read_text())
        d["not_admitted"].pop("lancedb")
        p.write_text(json.dumps(d))
        self.assertTrue(any("LanceDB" in e for e in validate(root)), validate(root))

    def test_driver_negative_control_defused_fails(self) -> None:
        # If someone weakens a driver assertion so a negative control no longer
        # goes red, the selftest (and thus validate) must fail.
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        drv = root / "scripts" / "code_intel_driver.py"
        t = drv.read_text()
        # defuse: make index_populated always true
        t = t.replace("chunk_count > 0", "True")
        drv.write_text(t)
        self.assertTrue(any("selftest" in e for e in validate(root)), validate(root))


if __name__ == "__main__":
    unittest.main()
