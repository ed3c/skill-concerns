from __future__ import annotations

import plistlib
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWEEP = ROOT / "scripts" / "maintain_skills.py"
PLIST = ROOT / "ops" / "com.neon.maintain-skills.plist"


class MaintainSkillsTests(unittest.TestCase):
    def test_selftest_passes(self) -> None:
        """Planted drift is detected, filed, never autofixed, and leaves no residue."""
        completed = subprocess.run(
            [sys.executable, str(SWEEP), "--selftest"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_sweep_gates_nothing(self) -> None:
        """N-class reader: no admission, stamp, or CI path may consume this sweep.

        The sweep re-runs gates but is not one. If any of these surfaces ever
        starts reading its exit code or its report, this test reds and the
        N-class claim in scripts/maintain_skills.py has to be withdrawn.
        """
        consumers = [
            ROOT / "scripts" / "run_all.py",
            ROOT / "scripts" / "admission_stamp.py",
            ROOT / "scripts" / "land_pr.py",
            ROOT / "scripts" / "check_admissions.py",
            ROOT / "scripts" / "check_skill_bundles.py",
            ROOT / "scripts" / "check_agents_hops.py",
            *sorted((ROOT / ".github" / "workflows").glob("*.yml")),
        ]
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in consumers
            if "maintain_skills" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual([], offenders)

    def test_launchd_plist_drives_this_sweep(self) -> None:
        """The cadence owner must name a script that exists in this tree."""
        plist = plistlib.loads(PLIST.read_bytes())
        self.assertEqual("com.neon.maintain-skills", plist["Label"])
        self.assertEqual(PLIST.stem, plist["Label"])
        arguments = plist["ProgramArguments"]
        self.assertTrue(
            arguments[1].endswith("scripts/maintain_skills.py"), arguments
        )
        self.assertTrue(SWEEP.is_file())
        self.assertIn("--report-dir", arguments)
        self.assertIn("StartCalendarInterval", plist)


if __name__ == "__main__":
    unittest.main()
