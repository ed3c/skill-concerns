from __future__ import annotations

import json
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

    def test_the_mirror_pin_files_its_drift_at_the_mirror(self) -> None:
        """ed3c/skill-concerns#97: the mirrored shape gains a mechanical reader.

        `validate_red_team.completeness_reasons()` is a declared mirror of the
        consumer's issue-admission gate, and nothing in this repository re-read
        the bytes it mirrors. The pin is that reader. This plants the drift the
        pin exists for -- the consumer's blob identity moves -- and reads the
        finding back at its own named destination, which must be the MIRROR and
        not the pin file: the pin is correct, the mirror is what has to be
        re-derived.
        """

        def fake_run(command, cwd, timeout=900):
            joined = " ".join(command)
            if "cursor/plugins" in joined:  # the neighbouring pin, unchanged
                if "commits/" in joined:
                    return {
                        "returncode": 0,
                        "stdout": "b9ddc83c32972210b8a94d389130713e8eed346e",
                        "tail": "",
                    }
                if "compare/" in joined:
                    return {"returncode": 0, "stdout": "identical", "tail": ""}
                return {
                    "returncode": 0,
                    "stdout": "a2680b91fead45a0b4963d8c367a854956bea59d"
                    if "maintain-verification" in joined
                    else "f869e26122991252373d5b8f6357e5b9ff195a00",
                    "tail": "",
                }
            if "issue_contract.py" in joined:  # the consumer moved
                return {"returncode": 0, "stdout": "f" * 40, "tail": ""}
            raise AssertionError(f"unexpected command: {command}")

        with mock.patch.object(maintain_skills, "_run", side_effect=fake_run):
            _, findings, unreachable = maintain_skills.check_upstream(ROOT, online=True)

        self.assertEqual([], unreachable)
        drift = [
            item
            for item in findings
            if item["diagnostic"] == "UPSTREAM_WATCHED_FILE_CHANGED"
        ]
        self.assertEqual(1, len(drift), findings)
        destination = drift[0]["destination"]
        self.assertTrue(
            destination.startswith("skills/red-team/scripts/validate_red_team.py:"),
            destination,
        )

        # Direct readback: open the destination and confirm the line it names
        # is the mirror's own definition, not a plausible-looking number.
        relative, line_number = destination.rsplit(":", 1)
        line = (ROOT / relative).read_text(encoding="utf-8").splitlines()[
            int(line_number) - 1
        ]
        self.assertIn("def completeness_reasons", line)

    def test_a_pin_with_no_commit_never_reports_a_moved_head(self) -> None:
        """The planted negative for the switch that keeps the cadence readable.

        A consumer repository's head moves daily. If a file-identity pin also
        watched the head, every sweep would report drift for a fact nobody is
        watching and the outcome would be permanently `changed`. Neither
        `UPSTREAM_MAIN_MOVED` nor `UPSTREAM_PIN_NOT_ANCESTOR` may come from a
        pin that names no commit -- and the provider must never be asked.
        """
        asked: list[str] = []

        def fake_run(command, cwd, timeout=900):
            joined = " ".join(command)
            asked.append(joined)
            if "cursor/plugins" in joined:
                if "commits/" in joined:
                    return {"returncode": 0, "stdout": "deadbeef" * 5, "tail": ""}
                if "compare/" in joined:
                    return {"returncode": 0, "stdout": "behind", "tail": ""}
                return {"returncode": 0, "stdout": "0" * 40, "tail": ""}
            return {"returncode": 0, "stdout": "f" * 40, "tail": ""}

        with mock.patch.object(maintain_skills, "_run", side_effect=fake_run):
            _, findings, _ = maintain_skills.check_upstream(ROOT, online=True)

        head_shaped = [
            item
            for item in findings
            if item["diagnostic"]
            in {"UPSTREAM_MAIN_MOVED", "UPSTREAM_PIN_NOT_ANCESTOR"}
            and "noodles" in item["detail"]
        ]
        self.assertEqual([], head_shaped, findings)
        self.assertEqual(
            [],
            [
                call
                for call in asked
                if "ed3c/noodles" in call and ("commits/" in call or "compare/" in call)
            ],
            asked,
        )

    def test_an_unchanged_upstream_resolves_clean(self) -> None:
        """Negative control: the pin can be green, so a red one means something."""
        document = json.loads(
            (ROOT / "policy" / "upstream-pins.json").read_text(encoding="utf-8")
        )
        blobs = {
            watched["path"]: watched["blob_sha"]
            for pin in document["pins"]
            for watched in pin.get("watched_files", [])
        }
        heads = {
            pin["repository"]: pin["pinned_commit"]
            for pin in document["pins"]
            if pin.get("pinned_commit")
        }

        def fake_run(command, cwd, timeout=900):
            joined = " ".join(command)
            if "compare/" in joined:
                return {"returncode": 0, "stdout": "identical", "tail": ""}
            for repository, sha in heads.items():
                if f"{repository}/commits/" in joined:
                    return {"returncode": 0, "stdout": sha, "tail": ""}
            for path, sha in blobs.items():
                if path in joined:
                    return {"returncode": 0, "stdout": sha, "tail": ""}
            raise AssertionError(f"unexpected command: {command}")

        with mock.patch.object(maintain_skills, "_run", side_effect=fake_run):
            _, findings, unreachable = maintain_skills.check_upstream(ROOT, online=True)
        self.assertEqual([], findings)
        self.assertEqual([], unreachable)

    def test_an_absent_mirror_is_named_rather_than_guessed(self) -> None:
        """A destination is never invented: absence and an anchor loss differ."""
        self.assertIsNone(maintain_skills.mirror_destination(ROOT, None))
        self.assertEqual(
            "MIRROR_ABSENT:skills/nowhere/nothing.py",
            maintain_skills.mirror_destination(
                ROOT, {"path": "skills/nowhere/nothing.py", "anchor": "def x"}
            ),
        )
        self.assertEqual(
            "MIRROR_ANCHOR_ABSENT:scripts/run_all.py:def completeness_reasons",
            maintain_skills.mirror_destination(
                ROOT,
                {"path": "scripts/run_all.py", "anchor": "def completeness_reasons"},
            ),
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
