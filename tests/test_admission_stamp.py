"""The admission stamper must be able to refuse.

Every receipt asserts `PASS` for controls nobody re-executed at stamp time. The
falsifier below plants one red in a scratch copy of the repository, runs a real
`gen_admission.py`, and requires a refusal with no receipt bytes written.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from admission_stamp import REFUSAL  # noqa: E402
from common import load_json  # noqa: E402
from run_all import SKILL_CHECKS  # noqa: E402

# The plant: this Skill's `test_hollow_topology_removed_fails` asserts the
# validator names a missing topology file. Renaming the diagnostic defuses that
# hollow control and turns the Skill's suite -- and only its suite -- red.
PLANT_SKILL = "spatial-loop-grounded"
PLANT_FILE = "skills/spatial-loop-grounded/scripts/validate_spatial_loop_grounded.py"
PLANT_OLD = "L1 domain/machine-topology.json missing"
PLANT_NEW = "L1 topology absent"


def scratch_copy(case: unittest.TestCase) -> Path:
    temp = tempfile.TemporaryDirectory(prefix="stamp-refusal-")
    case.addCleanup(temp.cleanup)
    root = Path(temp.name) / "repo"
    shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return root


def gen_admission(root: Path, skill: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, f"skills/{skill}/scripts/gen_admission.py"],
        cwd=root,
        capture_output=True,
        text=True,
    )


class AdmissionStampRefusalTests(unittest.TestCase):
    def test_planted_red_refuses_then_restored_green_stamps(self) -> None:
        root = scratch_copy(self)
        receipt = root / "admissions" / f"{PLANT_SKILL}.json"
        before = receipt.read_bytes()

        source = root / PLANT_FILE
        text = source.read_text(encoding="utf-8")
        self.assertIn(PLANT_OLD, text)
        source.write_text(text.replace(PLANT_OLD, PLANT_NEW, 1), encoding="utf-8")

        red = gen_admission(root, PLANT_SKILL)
        self.assertNotEqual(red.returncode, 0, red.stdout)
        self.assertIn(REFUSAL, red.stderr)
        self.assertNotIn("wrote", red.stdout)
        self.assertEqual(receipt.read_bytes(), before, "a refusal must not write bytes")

        source.write_text(text, encoding="utf-8")
        green = gen_admission(root, PLANT_SKILL)
        self.assertEqual(green.returncode, 0, green.stdout + green.stderr)
        self.assertIn("wrote", green.stdout)
        self.assertEqual(
            receipt.read_bytes(), before, "the committed receipt must be reproducible"
        )

    def test_refusal_survives_a_green_validator_with_a_red_suite(self) -> None:
        """The plant leaves the validator green, so the refusal can only come
        from unittest discovery actually running."""
        root = scratch_copy(self)
        source = root / PLANT_FILE
        text = source.read_text(encoding="utf-8")
        source.write_text(text.replace(PLANT_OLD, PLANT_NEW, 1), encoding="utf-8")

        validator = subprocess.run(
            [sys.executable, SKILL_CHECKS[PLANT_SKILL][0][0]],
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(validator.returncode, 0, validator.stdout + validator.stderr)
        self.assertIn("RED_CHECK", gen_admission(root, PLANT_SKILL).stderr)

    def test_every_registered_skill_stamps_through_the_shared_surface(self) -> None:
        for row in load_json(ROOT / "registry.json")["skills"]:
            name = row["name"]
            with self.subTest(skill=name):
                self.assertTrue(SKILL_CHECKS.get(name), f"no declared checks for {name}")
                producer = ROOT / row["path"] / "scripts" / "gen_admission.py"
                body = producer.read_text(encoding="utf-8")
                self.assertIn("from admission_stamp import stamp", body)
                self.assertIn(f'stamp("{name}")', body)
                # no per-Skill copy of the guard
                self.assertNotIn("subprocess", body)
                self.assertNotIn("json.dumps", body)

    def test_unknown_skill_refuses_rather_than_stamping_nothing(self) -> None:
        root = scratch_copy(self)
        import admission_stamp

        self.assertEqual(admission_stamp.stamp("not-a-skill", root), 1)
        self.assertFalse((root / "admissions" / "not-a-skill.json").exists())

    def test_receipt_controls_cover_every_eval_case(self) -> None:
        for row in load_json(ROOT / "registry.json")["skills"]:
            name = row["name"]
            with self.subTest(skill=name):
                receipt = load_json(ROOT / row["admission"])
                stamped = {control["id"] for control in receipt["controls"]}
                inventory = load_json(ROOT / row["path"] / "evals" / "cases.json")
                for case in inventory["cases"]:
                    self.assertIn(case["id"], stamped)


if __name__ == "__main__":
    unittest.main()
