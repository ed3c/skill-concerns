"""Eval harness for control-code-intel: positive controls + hollow mutations.

Every mutation models a way the three-layer skill could silently degrade; each
must FAIL the validator (or the L2 driver selftest). This is the hillclimb gate.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import code_intel_driver  # noqa: E402
import gen_receipts  # noqa: E402
from validate_control_code_intel import validate  # noqa: E402

TOPOLOGY = SKILL_ROOT / "domain" / "code-intel-topology.json"


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

    # ------------------------------------------------------------------
    # Environment contract, ed3c/skill-concerns#76. The stack was consumed as
    # ambient: present on the authoring host, declared nowhere. These arms
    # exercise the two halves of the cure - the declaration is read, and the
    # live path refuses by name when a declared tool is not on a real PATH.

    def path_with(self, *commands: str) -> str:
        """A PATH containing exactly these executables and nothing else."""
        temp = tempfile.TemporaryDirectory(prefix="cci-path-")
        self.addCleanup(temp.cleanup)
        for command in commands:
            binary = Path(temp.name) / command
            binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
        return temp.name

    def declared_path_tools(self) -> list[str]:
        topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
        return sorted(
            tool["presence"]["probe"]
            for tool in topology["tools"].values()
            if tool.get("presence", {}).get("kind") == "path"
        )

    def preflight_on(self, path: str) -> tuple[int, str]:
        result = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "code_intel_driver.py"), "--preflight"],
            capture_output=True,
            text=True,
            env={**os.environ, "PATH": path},
        )
        return result.returncode, result.stdout + result.stderr

    def test_preflight_refuses_naming_the_tool_absent_from_a_real_path(self) -> None:
        # Planted control by PATH manipulation: an empty PATH is a host where
        # the declared stack is not installed. Every path-kind tool must be
        # named, and the exit must be the tool-absent one.
        probes = self.declared_path_tools()
        self.assertTrue(probes, "no path-kind tool is declared, so nothing is being checked")
        code, output = self.preflight_on(self.path_with())
        self.assertEqual(code_intel_driver.EXIT_TOOL_ABSENT, code, output)
        for probe in probes:
            self.assertIn(f"{probe!r} is not on PATH", output)

    def test_preflight_passes_when_every_declared_tool_is_on_path(self) -> None:
        # The other direction: without it the refusal above could be a preflight
        # that refuses unconditionally.
        code, output = self.preflight_on(self.path_with(*self.declared_path_tools()))
        self.assertEqual(0, code, output)
        self.assertIn("preflight OK", output)

    def test_tool_absence_and_a_red_assertion_are_different_states(self) -> None:
        # The representation claim, run rather than asserted about: both
        # failures are produced for real - a host with no stack on PATH, and a
        # driver whose assertion has been defused so a negative control stops
        # going red - and the two must not come back wearing the same code.
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        driver = root / "scripts" / "code_intel_driver.py"
        driver.write_text(driver.read_text().replace("chunk_count > 0", "True"))
        red = subprocess.run(
            [sys.executable, str(driver), "--selftest"], capture_output=True, text=True
        )
        absent, absent_output = self.preflight_on(self.path_with())
        self.assertEqual(code_intel_driver.EXIT_ASSERTION_RED, red.returncode, red.stdout)
        self.assertEqual(code_intel_driver.EXIT_TOOL_ABSENT, absent, absent_output)
        self.assertNotEqual(red.returncode, absent)

    def test_a_tool_consuming_the_environment_without_a_declaration_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "domain" / "code-intel-topology.json"
        document = json.loads(path.read_text())
        document["tools"]["grepai"].pop("presence")
        path.write_text(json.dumps(document))
        self.assertTrue(
            any("presence declaration" in e for e in validate(root)), validate(root)
        )

    def test_an_ambient_declaration_without_a_prerequisite_fails(self) -> None:
        # Ambient is admitted; ambient-with-nothing-said is the defect. Dropping
        # the prerequisite leaves a tool that claims to be someone else's
        # problem without saying whose.
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "domain" / "code-intel-topology.json"
        document = json.loads(path.read_text())
        document["tools"]["serena"]["presence"].pop("prerequisite")
        path.write_text(json.dumps(document))
        self.assertTrue(
            any("prerequisite" in e for e in validate(root)), validate(root)
        )

    def test_no_tracked_file_carries_a_host_absolute_path(self) -> None:
        # The grep readback of ed3c/skill-concerns#76's first acceptance, as a
        # standing test rather than a one-time command in a report.
        #
        # The needles are assembled rather than written: this file is itself a
        # tracked file under the root being scanned, so a literal here would be
        # the very byte the assertion forbids and the check would fail on its
        # own text. Split so the operator's own grep readback stays honest.
        needles = ("/" + "Users" + "/", "/" + "home" + "/")
        offenders = []
        for path in sorted(SKILL_ROOT.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for needle in needles:
                if needle in text:
                    offenders.append(f"{path.relative_to(SKILL_ROOT).as_posix()}:{needle}")
        self.assertEqual([], offenders)

    # ------------------------------------------------------------------
    # The producer field's author, ed3c/skill-concerns#84. These fields were
    # right and hand-written; what is asserted here is that they are now a
    # function of an execution, and that the function refuses rather than
    # guesses. A generator that only ever ran against a conformant file has
    # never refused anything.

    def committed(self) -> dict:
        return json.loads((SKILL_ROOT / "receipts.json").read_text(encoding="utf-8"))

    def test_the_committed_receipts_are_what_the_producer_makes(self) -> None:
        results = gen_receipts.run_driver()
        self.assertEqual(
            (SKILL_ROOT / "receipts.json").read_text(encoding="utf-8"),
            gen_receipts.render(self.committed(), results),
        )

    def test_a_receipt_naming_an_assertion_that_does_not_exist_is_refused(self) -> None:
        results = gen_receipts.run_driver()
        results.pop("index_populated")
        with self.assertRaises(gen_receipts.ReceiptRefused) as caught:
            gen_receipts.build(self.committed(), results)
        self.assertIn("RECEIPT_ASSERTION_ABSENT:last-index-time-gotcha", str(caught.exception))

    def test_a_receipt_whose_assertion_reds_is_refused(self) -> None:
        results = gen_receipts.run_driver()
        results["index_populated"] = False
        with self.assertRaises(gen_receipts.ReceiptRefused) as caught:
            gen_receipts.build(self.committed(), results)
        self.assertIn("RECEIPT_ASSERTION_RED:last-index-time-gotcha", str(caught.exception))

    def test_an_entry_claiming_the_driver_with_no_correspondence_is_refused(self) -> None:
        # The exact shape #84 names: a producer field typed by hand for a claim
        # nothing replays. HOST_OBSERVED is the earned default, and this is the
        # refusal that keeps it from being an escape hatch in reverse.
        document = self.committed()
        document["evidence"]["pgvector-built-pg16"]["producer"] = gen_receipts.DRIVER
        with self.assertRaises(gen_receipts.ReceiptRefused) as caught:
            gen_receipts.build(document, gen_receipts.run_driver())
        self.assertIn("RECEIPT_PRODUCER_UNEARNED:pgvector-built-pg16", str(caught.exception))

    def test_a_hand_edited_receipts_file_reds_the_validator(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "receipts.json"
        document = json.loads(path.read_text())
        document["evidence"]["grepai-mcp-connected"]["producer"] = "scripts/code_intel_driver.py"
        path.write_text(json.dumps(document, indent=2) + "\n")
        self.assertTrue(
            any("RECEIPT_PRODUCER_UNEARNED" in e for e in validate(root)), validate(root)
        )


if __name__ == "__main__":
    unittest.main()
