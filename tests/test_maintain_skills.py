from __future__ import annotations

import json
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import maintain_skills  # noqa: E402
import run_all  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SWEEP = ROOT / "scripts" / "maintain_skills.py"
PLIST = ROOT / "ops" / "com.neon.maintain-skills.plist"
WORKFLOWS = ROOT / ".github" / "workflows"

# The one workflow allowed to name the sweep (ed3c/skill-concerns#134).
CADENCE_WORKFLOW = WORKFLOWS / "maintain.yml"

# Invocation is allowed; consumption is not, and the two are different bytes.
#
# A workflow that only RUNS the sweep leaves no edge an admission path can
# follow: nothing waits on its job, no other workflow triggers on its
# completion, and it never runs on a pull request or a push, so branch
# protection has no check to require. Each shape below is one YAML key a reader
# can point at, because this repository has no YAML parser available to its
# gates and a rule nothing can run is not a rule.
#
# Comment-only lines are skipped so the file can DESCRIBE the shapes it must
# not contain. An inline trailing comment after a real key still counts, which
# is the fail-closed direction: a false positive costs one reworded comment, a
# false negative ships a consumed sweep.
#
# This table is a DENYLIST and is therefore not the whole rule: it can only
# refuse a shape somebody thought of, and GitHub's trigger vocabulary grows
# (`workflow_call:` alone would make this sweep a reusable workflow another job
# `uses:`, with `outputs:` a consumer reads, and no key below says a word about
# it). `TRIGGER_ALLOWLIST` closes that direction: what this file may be
# triggered BY is enumerated positively, so an event nobody here has heard of
# reds on arrival instead of on the day someone adds a row. The denylist keeps
# the shapes an allowlist over triggers cannot see -- `needs:` lives inside a
# job, not under `on:`.
CONSUMPTION_SHAPES = {
    "needs:": "a job another job waits on",
    "workflow_run": "a completion another workflow triggers on",
    "pull_request": "a run branch protection could require",
    "push:": "a run branch protection could require",
}

# Every event the cadence workflow may run on. A clock and a human, nothing
# else: both are entered from outside the admission path and neither hands a
# result back to it.
TRIGGER_ALLOWLIST = ["schedule", "workflow_dispatch"]


def workflow_directives(text: str) -> str:
    """The lines a YAML reader acts on. A comment-only line is prose."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def trigger_keys(text: str) -> list[str]:
    """The event keys under the top-level `on:` block, in file order.

    Two-space keys only, so `- cron:` under `schedule:` is an argument to a
    trigger rather than a trigger, and the first unindented line ends the
    block. Enough of a reader for a rule to run on, which is the bar here: the
    gates in this repository have no YAML parser available to them.
    """
    keys: list[str] = []
    inside = False
    for line in workflow_directives(text).splitlines():
        if line.startswith("on:"):
            inside = True
            continue
        if not inside:
            continue
        if line[:1] not in {" ", "\t", ""}:
            break
        found = re.match(r"  (\w+):", line)
        if found:
            keys.append(found.group(1))
    return keys


def consumption_offenses(text: str) -> list[str]:
    """Every way `text` would let some surface consume the sweep's result."""
    directives = workflow_directives(text)
    offenses = [
        f"{token}: {why}"
        for token, why in CONSUMPTION_SHAPES.items()
        if token in directives
    ]
    offenses += [
        f"on: {key}: not an entry this workflow may be triggered by"
        for key in trigger_keys(text)
        if key not in TRIGGER_ALLOWLIST
    ]
    return sorted(offenses)


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

    def test_the_sweep_drives_every_repository_gate_the_runner_runs(self) -> None:
        """The gate list is DERIVED, so a hand copy cannot drift again.

        It had drifted: `check_receipt_provenance.py` ran in
        `scripts/run_all.py` and was absent from the sweep's own tuple, so the
        sweep reported the repository gates green having never run one of them
        (ed3c/skill-concerns#102). Two arms. The identity is asserted against
        `run_all` because that is the owning declaration, and then the argv the
        sweep actually builds is read back - a tuple that agreed while the rows
        were built from something else would pass the first arm alone. The
        second is also the vacuity guard: the drifted gate is named here by
        hand, so a future edit that quietly narrows either side reds.
        """
        self.assertEqual(maintain_skills.REPO_GATES, run_all.REPO_GATES)
        self.assertIn("check_receipt_provenance.py", maintain_skills.REPO_GATES)
        driven = [
            Path(argv[0]).name
            for subject, argv in maintain_skills.check_rows(ROOT, run_skill_checks=False)
            if subject.startswith("repository:")
        ]
        self.assertEqual(list(run_all.REPO_GATES), driven)

    def test_sweep_gates_nothing(self) -> None:
        """N-class reader: no admission, stamp, or CI path may consume this sweep.

        The sweep re-runs gates but is not one. If any surface ever starts
        reading its exit code or its report, this test reds and the N-class
        claim in scripts/maintain_skills.py has to be withdrawn.

        The consumer list is every script in scripts/ and every workflow,
        globbed rather than hand-enumerated - a hardcoded list goes stale
        the day a new script (e.g. scripts/common.py, scripts/freeze_source.py)
        starts naming this sweep and nobody remembers to add it here.

        One workflow is exempt, and only one (ed3c/skill-concerns#134). The
        stated rule was always about CONSUMPTION - "if any surface starts
        reading its exit code or its report" - while the implemented rule was a
        substring scan that could not tell a workflow that RUNS the sweep from
        a gate that consumes it, so the rule protecting the N-class property
        was also the rule denying the sweep a clock. CADENCE_WORKFLOW is that
        one file and it is held to the harder half by
        `test_the_cadence_workflow_invokes_without_being_consumed`; every other
        workflow, and every other script, still may not name the sweep at all.
        """
        consumers = [
            path
            for path in sorted((ROOT / "scripts").glob("*.py"))
            if path.name != "maintain_skills.py"
        ] + [
            path
            for path in sorted(WORKFLOWS.glob("*.yml"))
            if path != CADENCE_WORKFLOW
        ]
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in consumers
            if "maintain_skills" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual([], offenders)

    def test_the_cadence_workflow_invokes_without_being_consumed(self) -> None:
        """The exemption is not a hole: the one allowed file is held tighter.

        It must actually run the sweep (an exemption for a workflow that does
        not invoke it would be an exemption for nothing), it must run on a
        clock, it must carry none of the shapes that would give an admission
        path an edge into it, and no other workflow may trigger on its name.
        """
        text = CADENCE_WORKFLOW.read_text(encoding="utf-8")
        directives = workflow_directives(text)
        # Every arm reads the directives, never the prose: a workflow that only
        # DESCRIBED running the sweep would otherwise satisfy this.
        self.assertIn("scripts/maintain_skills.py", directives)
        self.assertIn("schedule:", directives)
        self.assertIn("cron:", directives)
        self.assertEqual([], consumption_offenses(text))
        # Positively, not by absence of the shapes anyone happened to list: the
        # events this file may be entered by are exactly these two, so a
        # `workflow_call:` (which would make the sweep a reusable workflow with
        # outputs a caller reads) or a `repository_dispatch:` reds without
        # anybody having to have anticipated it.
        self.assertEqual(TRIGGER_ALLOWLIST, trigger_keys(text))
        # SHADOW only: the invocation nobody watches must not carry the half
        # with a write verb, exactly as the launchd row must not.
        self.assertNotIn("--pass", directives)

        name = re.search(r"^name:[ \t]*(\S+)", directives, re.MULTILINE).group(1)
        for path in sorted(WORKFLOWS.glob("*.yml")):
            if path == CADENCE_WORKFLOW:
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.lstrip().startswith("workflows:"):
                    self.assertNotIn(name, line, path.name)

    def test_a_consuming_edge_still_reds_the_same_rule(self) -> None:
        """The planted control ed3c/skill-concerns#134 asks for.

        The widening admits invocation and must still refuse consumption, so
        the same function that passes the committed file has to red on each
        shape added to it. Four denylisted shapes, and then the two the
        denylist never mentions: `workflow_call:` and `repository_dispatch:`
        are refused by the trigger allowlist instead, which is the arm that
        says the rule does not depend on somebody having thought of them.
        """
        text = CADENCE_WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual([], consumption_offenses(text))
        for planted in (
            "    needs: [verify]\n",
            "  workflow_run:\n    workflows: [verify]\n",
            "  pull_request:\n",
            "  push:\n",
        ):
            with self.subTest(planted=planted.strip()):
                self.assertNotEqual([], consumption_offenses(text + planted))
        # Inside the `on:` block, where a trigger actually goes. Appending to
        # the end of the file would land after `permissions:` and prove nothing
        # about triggers.
        entered = "  workflow_dispatch:\n"
        self.assertIn(entered, text)
        for planted in ("  workflow_call:\n", "  repository_dispatch:\n"):
            with self.subTest(planted=planted.strip()):
                mutated = text.replace(entered, entered + planted, 1)
                self.assertNotEqual([], consumption_offenses(mutated))
                self.assertNotEqual(TRIGGER_ALLOWLIST, trigger_keys(mutated))
        # And prose about the shapes is not the shapes: a comment naming them
        # must not red, or the file could not document its own rule.
        self.assertEqual(
            [], consumption_offenses(text + "\n# no needs: edge, no workflow_run\n")
        )

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

        # Every source-lock-derived watch answers with its own pinned blob, so
        # the ONE drift in this pass is the mirrored consumer file and the
        # count assertion below stays a real count (ed3c/skill-concerns#54).
        pinned = {
            f"repos/{pin['repository']}/contents/{watched['path']}": watched["blob_sha"]
            for pin in maintain_skills.source_lock_pins(ROOT)[0]
            for watched in pin["watched_files"]
        }

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
            for token, sha in pinned.items():
                if token in joined:
                    return {"returncode": 0, "stdout": sha, "tail": ""}
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
        # Keyed by the whole `repos/<slug>/contents/<path>` token the sweep
        # actually issues, not by path alone: once the source locks are watched
        # too (ed3c/skill-concerns#54), four different providers serve a file
        # called AGENTS.md and a bare-path match answers with whichever one the
        # dict happened to yield first.
        blobs = {
            f"repos/{pin['repository']}/contents/{watched['path']}": watched["blob_sha"]
            for pin in document["pins"] + maintain_skills.source_lock_pins(ROOT)[0]
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
            for token, sha in blobs.items():
                if token in joined:
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


class SourceLockPinTests(unittest.TestCase):
    """ed3c/skill-concerns#54: an admitted Skill's method references get re-read.

    The claim under test is about the WIRE, not the parse. Asserting that
    `source_lock_pins()` returns what the locks contain would be a tautology -
    it reads them. What is falsifiable is that `check_upstream` issues a
    provider call for each one, that a moved blob comes back as a finding filed
    at the lock line, and that the two documented exits (a candidate, and a
    repository token this sweep cannot address) behave as written rather than
    disappearing into the same silence as "nothing to watch".
    """

    def locked_references(self) -> list[tuple[str, str, str]]:
        """(skill, repository, path) straight from the lock bytes, not the pins."""
        rows: list[tuple[str, str, str]] = []
        for lock in sorted(ROOT.glob("intake/*/source-lock.json")):
            skill = lock.parent.name
            if not (ROOT / "admissions" / f"{skill}.json").is_file():
                continue
            document = json.loads(lock.read_text(encoding="utf-8"))
            for reference in document.get("method_references", []):
                rows.append((skill, reference["repository"], reference["path"]))
        return rows

    def test_every_admitted_method_reference_reaches_the_provider(self) -> None:
        """The gap #54 names: these were pinned at admission and never re-read."""
        asked: list[str] = []

        def fake_run(command, cwd, timeout=900):
            asked.append(" ".join(command))
            if "compare/" in " ".join(command):
                return {"returncode": 0, "stdout": "identical", "tail": ""}
            return {"returncode": 0, "stdout": "0" * 40, "tail": ""}

        with mock.patch.object(maintain_skills, "_run", side_effect=fake_run):
            maintain_skills.check_upstream(ROOT, online=True)

        rows = self.locked_references()
        self.assertTrue(rows, "no admitted Skill carries method_references at all")
        for skill, repository, path in rows:
            with self.subTest(skill=skill, path=path):
                slug = maintain_skills.provider_slug(repository)
                self.assertIsNotNone(slug, repository)
                self.assertTrue(
                    any(f"repos/{slug}/contents/{path}" in call for call in asked),
                    f"{skill} pins {slug}:{path} and no provider call names it",
                )

        # One call per FILE, not one per Skill that cites it: three Skills and
        # `policy/upstream-pins.json` all name the same two pstack documents.
        # Counted on the addressed file rather than the raw argv, because the
        # policy pin asks `?ref=main` and a derived pin asks the default branch
        # -- two different strings naming one blob, which a raw-string count
        # would report as two legitimate calls.
        fetched = [
            call.split("/contents/", 1)[1].split("?")[0].split(" ")[0]
            + "@"
            + call.split("repos/", 1)[1].split("/contents/")[0]
            for call in asked
            if "/contents/" in call
        ]
        self.assertEqual(sorted(set(fetched)), sorted(fetched), fetched)

    def test_a_moved_method_reference_blob_files_drift_at_its_source_lock(self) -> None:
        """Prove it reds: this branch was never reachable before #54."""
        subject = json.loads(
            (ROOT / "intake" / "context-closure-engineering" / "source-lock.json").read_text(
                encoding="utf-8"
            )
        )["method_references"][0]
        moved = subject["blob_sha"]

        def fake_run(command, cwd, timeout=900):
            joined = " ".join(command)
            if "compare/" in joined:
                return {"returncode": 0, "stdout": "identical", "tail": ""}
            if "commits/" in joined:
                return {
                    "returncode": 0,
                    "stdout": "b9ddc83c32972210b8a94d389130713e8eed346e",
                    "tail": "",
                }
            if f"repos/ed3c/noodles/contents/{subject['path']}" in joined:
                return {"returncode": 0, "stdout": "e" * 40, "tail": ""}
            document = json.loads(
                (ROOT / "policy" / "upstream-pins.json").read_text(encoding="utf-8")
            )
            everything = document["pins"] + maintain_skills.source_lock_pins(ROOT)[0]
            for pin in everything:
                for watched in pin.get("watched_files", []):
                    token = f"repos/{pin['repository']}/contents/{watched['path']}"
                    if token in joined:
                        return {"returncode": 0, "stdout": watched["blob_sha"], "tail": ""}
            raise AssertionError(f"unexpected command: {command}")

        with mock.patch.object(maintain_skills, "_run", side_effect=fake_run):
            _, findings, unreachable = maintain_skills.check_upstream(ROOT, online=True)

        self.assertEqual([], unreachable)
        drift = [f for f in findings if f["diagnostic"] == "UPSTREAM_WATCHED_FILE_CHANGED"]
        self.assertEqual(1, len(drift), findings)
        self.assertEqual(moved, drift[0]["subject"])

        # Readback: the destination must be the lock line carrying that blob,
        # not a plausible-looking path:1.
        relative, number = drift[0]["destination"].rsplit(":", 1)
        line = (ROOT / relative).read_text(encoding="utf-8").splitlines()[int(number) - 1]
        self.assertIn(moved, line)
        self.assertTrue(relative.startswith("intake/"), relative)

    def test_a_candidate_without_a_receipt_is_not_yet_the_subject(self) -> None:
        """The ADMITTED gate is the receipt, and it is load-bearing.

        `intake/agent-friendly-architecture-compiler` is a candidate on an
        unlanded PR (ed3c/skill-concerns#19). Its provider resolves and its
        pinned commit still serves both frozen blobs, but neither watched path
        is on that provider's default branch any more, so watching it would park
        the sweep on `changed` forever over bytes no receipt binds.
        """
        candidates = [
            lock.parent.name
            for lock in sorted(ROOT.glob("intake/*/source-lock.json"))
            if not (ROOT / "admissions" / f"{lock.parent.name}.json").is_file()
        ]
        self.assertIn("agent-friendly-architecture-compiler", candidates)
        watched = {pin["id"] for pin in maintain_skills.source_lock_pins(ROOT)[0]}
        for skill in candidates:
            self.assertNotIn(f"source-lock:{skill}", watched)

    def test_a_repository_this_sweep_cannot_address_is_reported_not_dropped(self) -> None:
        """Absence and unreadability never look alike (the check_refs precedent)."""
        for token in ("cursor/plugins", "https://github.com/ed3c/noodles"):
            with self.subTest(token=token):
                self.assertIsNotNone(maintain_skills.provider_slug(token))
        for token in ("https://github.com/ed3c/skills-shared.git",):
            self.assertEqual("ed3c/skills-shared", maintain_skills.provider_slug(token))
        for token in (None, "", "/Users/neon/github_projects/plugins", "not a repo at all"):
            with self.subTest(token=token):
                self.assertIsNone(maintain_skills.provider_slug(token))

        root = Path(tempfile.mkdtemp(prefix="source-lock-pins-"))
        self.addCleanup(shutil.rmtree, root, True)
        (root / "admissions").mkdir()
        (root / "admissions" / "demo.json").write_text("{}\n", encoding="utf-8")
        (root / "intake" / "demo").mkdir(parents=True)
        (root / "intake" / "demo" / "source-lock.json").write_text(
            json.dumps(
                {
                    "method_references": [
                        {
                            "repository": "/Users/neon/github_projects/plugins",
                            "path": "pstack/skills/create-verification-skill/SKILL.md",
                            "blob_sha": "f869e26122991252373d5b8f6357e5b9ff195a00",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        pins, unreadable = maintain_skills.source_lock_pins(root)
        self.assertEqual([], pins)
        self.assertEqual(1, len(unreadable), unreadable)
        self.assertIn("/Users/neon/github_projects/plugins", unreadable[0]["prerequisite"])


if __name__ == "__main__":
    unittest.main()
