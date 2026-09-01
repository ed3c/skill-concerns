"""Eval harness for dynamic-workflow: positive controls + hollow mutations.

Every mutation models a way this reader could silently degrade -- the K10 law
defused, a ceremony term restated instead of pointed at, a judge rule dropped
from judge-prompt, the reader growing an exec surface it could invoke
maintenance with. Each must FAIL the validator (or the L2 driver selftest that
validator runs). This is the hillclimb gate.

`monitor-prompt` and `judge-prompt` are declared executable routes in
`skill.json`; naming them here is what proves those routes are reached
(`check_skill_bundles.scan_hollow_execution_routes`).
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

from validate_dynamic_workflow import validate  # noqa: E402
import liveness_driver  # noqa: E402

DRIVER = SKILL_ROOT / "scripts" / "liveness_driver.py"
PROMPTS = SKILL_ROOT / "references" / "prompts"


def mutated_copy() -> tuple[tempfile.TemporaryDirectory, Path]:
    temp = tempfile.TemporaryDirectory(prefix="dwf-eval-")
    root = Path(temp.name) / "skill"
    shutil.copytree(SKILL_ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
    return temp, root


class DynamicWorkflowEvals(unittest.TestCase):
    # ---- positive controls -------------------------------------------------
    def test_positive_control_passes(self) -> None:
        self.assertEqual(validate(SKILL_ROOT), [])

    def test_l2_driver_selftest_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(DRIVER), "--selftest"], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dispatcher_prompt_files_are_referencable(self) -> None:
        """The prompts exist as files, so a dispatcher can cite a path, not a paste."""
        self.assertTrue((PROMPTS / "monitor-prompt.md").is_file())
        self.assertTrue((PROMPTS / "judge-prompt.md").is_file())

    def test_observation_evidence_survives_the_run(self) -> None:
        """create-verification-skill step 4: the proof outlives the run."""
        with tempfile.TemporaryDirectory(prefix="dwf-evidence-") as scratch:
            out = Path(scratch) / "observation.json"
            report = liveness_driver.observe(
                SKILL_ROOT / "evals" / "fixtures" / "healthy-wave",
                "claude-code-workflow",
                liveness_driver.parse_iso("2026-09-01T12:00:00Z"),
                out,
            )
            self.assertTrue(out.is_file())
            self.assertEqual(report["lens"], "ok")
            self.assertEqual(report["maintain_pass"], "NOT_SCHEDULED")
            self.assertEqual(report["summary"]["dead"], 0)

    # ---- hollow mutations --------------------------------------------------
    def test_missing_layer_file_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        (root / "references" / "portable-supervision-policy.md").unlink()
        self.assertTrue(any("L-layer" in e or "L0" in e for e in validate(root)), validate(root))

    def test_age_alone_declaring_death_fails(self) -> None:
        """Defuse K10 so silence becomes death: the selftest must go red."""
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        driver = root / "scripts" / "liveness_driver.py"
        driver.write_text(driver.read_text().replace('return "stalled-suspect"', 'return "dead"'))
        self.assertTrue(any("selftest" in e for e in validate(root)), validate(root))

    def test_death_signature_defused_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        driver = root / "scripts" / "liveness_driver.py"
        driver.write_text(
            driver.read_text().replace("if death_signature is not None:", "if False:")
        )
        self.assertTrue(any("selftest" in e for e in validate(root)), validate(root))

    def test_restated_ceremony_term_fails(self) -> None:
        """Point at control-noodle, never restate it."""
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "domain" / "dispatch-runtime-topology.json"
        topology = json.loads(path.read_text())
        term = topology["ceremony_boundary"]["not_owned_here"][0]
        topology["runtimes"]["codex-noodle-session"]["restated"] = f"{term} correctness lives here now"
        path.write_text(json.dumps(topology, indent=2))
        self.assertTrue(any("restates ceremony term" in e for e in validate(root)), validate(root))

    def test_k10_removed_from_topology_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "domain" / "dispatch-runtime-topology.json"
        topology = json.loads(path.read_text())
        topology["classes"]["dead"].pop("age_alone_insufficient")
        path.write_text(json.dumps(topology, indent=2))
        self.assertTrue(
            any("age_alone_insufficient" in e for e in validate(root)), validate(root)
        )

    def test_judge_rule_removed_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "references" / "prompts" / "judge-prompt.md"
        path.write_text(path.read_text().replace("ANSWERED-RESIDUE", "some other rule"))
        self.assertTrue(any("ANSWERED-RESIDUE" in e for e in validate(root)), validate(root))

    def test_unbacked_receipt_removed_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "receipts.json"
        receipts = json.loads(path.read_text())
        receipts["evidence"].pop("step-4-real-wave-observation")
        path.write_text(json.dumps(receipts))
        self.assertTrue(
            any("step-4-real-wave-observation" in e for e in validate(root)), validate(root)
        )

    def test_reader_gaining_exec_surface_fails(self) -> None:
        """A reader that can spawn a process can invoke maintenance inline."""
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        driver = root / "scripts" / "liveness_driver.py"
        driver.write_text("import subprocess\n" + driver.read_text())
        self.assertTrue(any("write/exec surface" in e for e in validate(root)), validate(root))

    # ---- adjudication 3: triggered, never applied ---------------------------
    def test_red_selftest_degrades_report_to_lens_suspect(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "domain" / "dispatch-runtime-topology.json"
        topology = json.loads(path.read_text())
        # A threshold no stall can cross: the planted stuck fixture stops being
        # detected, so the lens is provably broken now.
        topology["stall_threshold_seconds"] = 10**9
        path.write_text(json.dumps(topology, indent=2))

        with tempfile.TemporaryDirectory(prefix="dwf-degraded-") as scratch:
            out = Path(scratch) / "observation.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "liveness_driver.py"),
                    "--observe",
                    str(root / "evals" / "fixtures" / "stuck-wave"),
                    "--now",
                    "2026-09-01T12:00:00Z",
                    "--out",
                    str(out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(out.read_text())

        self.assertEqual(report["lens"], "lens-suspect")
        self.assertEqual(report["maintain_pass"], "SCHEDULED")
        finding = report["findings"][0]
        self.assertEqual(finding["type"], "lens-drift")
        self.assertEqual(finding["owner"], "dynamic-workflow")
        self.assertIn(":", finding["destination"])
        self.assertIn("SCHEDULED", finding["action"])


if __name__ == "__main__":
    unittest.main()
