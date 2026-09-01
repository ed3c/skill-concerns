from __future__ import annotations

import plistlib
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import maintain_skills  # noqa: E402


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

        The sweep re-runs gates but is not one. If any surface ever starts
        reading its exit code or its report, this test reds and the N-class
        claim in scripts/maintain_skills.py has to be withdrawn.

        The consumer list is every script in scripts/ and every workflow,
        globbed rather than hand-enumerated - a hardcoded list goes stale
        the day a new script (e.g. scripts/common.py, scripts/freeze_source.py)
        starts naming this sweep and nobody remembers to add it here.
        """
        consumers = [
            path
            for path in sorted((ROOT / "scripts").glob("*.py"))
            if path.name != "maintain_skills.py"
        ] + sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in consumers
            if "maintain_skills" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual([], offenders)

    def test_check_upstream_flags_all_three_drift_diagnostics(self) -> None:
        """Planted drift on the wire: each finding branch must actually red.

        The three check_upstream diagnostics were previously only observed
        in their green (matching) direction. This mocks `gh api` to return
        a moved head, a non-ancestor compare, and a changed watched blob in
        one pass, and asserts all three diagnostics fire.
        """

        def fake_run(command, cwd, timeout=900):
            joined = " ".join(command)
            if "commits/" in joined:
                return {"returncode": 0, "stdout": "deadbeef" * 5, "tail": ""}
            if "compare/" in joined:
                return {"returncode": 0, "stdout": "behind", "tail": ""}
            if "contents/" in joined:
                return {"returncode": 0, "stdout": "0" * 40, "tail": ""}
            raise AssertionError(f"unexpected command: {command}")

        with mock.patch.object(maintain_skills, "_run", side_effect=fake_run):
            _, findings, unreachable = maintain_skills.check_upstream(ROOT, online=True)
        diagnostics = {f["diagnostic"] for f in findings}
        self.assertEqual([], unreachable)
        self.assertEqual(
            {"UPSTREAM_MAIN_MOVED", "UPSTREAM_PIN_NOT_ANCESTOR", "UPSTREAM_WATCHED_FILE_CHANGED"},
            diagnostics,
        )

    def test_check_upstream_online_failure_degrades_the_outcome(self) -> None:
        """A genuine online provider failure must not look like --offline.

        check_refs already turns a failed read into pins state=BLOCKED so
        sweep() degrades the outcome. check_upstream previously only ever
        recorded such failures in `unreachable`, so an online run hitting a
        rate-limited or flaky cursor/plugins still reported "clean" with the
        entire upstream-pin subject silently absent.
        """

        def fake_run(command, cwd, timeout=900):
            return {"returncode": 1, "stdout": "", "tail": "gh: rate limit exceeded"}

        with mock.patch.object(maintain_skills, "_run", side_effect=fake_run):
            results, _, unreachable = maintain_skills.check_upstream(ROOT, online=True)
        self.assertTrue(unreachable, "the failure must still be listed with its prerequisite")
        self.assertTrue(
            any(item["state"] == "BLOCKED" for item in results),
            f"results={results}",
        )

    def test_the_write_verb_is_opt_in_and_the_cadence_never_takes_it(self) -> None:
        """SHADOW is the default; BUILD is reachable only through `--pass`.

        ed3c/skill-concerns#62 goal 1. The daily launchd row is the one
        invocation nobody watches, so it is the one that must never carry the
        half with a write verb. `mode` in the report says which half ran
        rather than leaving a reader to infer it from what did not happen.
        """
        self.assertNotIn("--pass", plistlib.loads(PLIST.read_bytes())["ProgramArguments"])
        report = maintain_skills.sweep(ROOT, run_skill_checks=False, online=False)
        self.assertEqual("shadow", report["mode"])
        self.assertTrue(report["edit_scope"]["held"], report["edit_scope"])

    def test_maintain_docs_carry_the_sc59_adjudications(self) -> None:
        """ed3c/skill-concerns#62 goal 4: adjudications live as tree bytes.

        Three owner rulings were reachable only as comments on
        ed3c/skill-concerns#59 - a destination no gate reads and no clone
        carries. This is the mechanical reader that keeps them here: delete
        a ruling from AGENTS.md and this reds.
        """
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("ed3c/skill-concerns#59", text)
        for adjudication in (
            "Runtime/ceremony boundary",
            "Filing-not-reflex coupling",
            "Trigger-not-apply exception",
        ):
            with self.subTest(adjudication=adjudication):
                self.assertIn(adjudication, text)

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
