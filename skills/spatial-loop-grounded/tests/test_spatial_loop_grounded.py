"""Eval harness for spatial-loop-grounded: positive control + hollow mutations.

Each mutation models a way the skill could silently degrade; every one must
FAIL the validator. This suite is the hillclimb gate for evals/cases.json.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_spatial_loop_grounded import entry_digest, validate  # noqa: E402
from gen_ledger import check_prefix_preserved  # noqa: E402
import ab_campaign  # noqa: E402

BEHAVIORAL = Path("evals/behavioral.json")
LEDGER = Path("evals/behavioral-campaigns/ledger.json")
AB = SKILL_ROOT / "evals" / "behavioral-campaigns" / "ab"


def rewrite_json(path: Path, mutate) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def mutated_copy() -> tuple[tempfile.TemporaryDirectory, Path]:
    temp = tempfile.TemporaryDirectory(prefix="slg-eval-")
    root = Path(temp.name) / "skill"
    shutil.copytree(SKILL_ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
    return temp, root


class SpatialLoopGroundedEvals(unittest.TestCase):
    def test_positive_control_passes(self) -> None:
        self.assertEqual(validate(SKILL_ROOT), [])

    def mutate_skill(self, old: str, new: str) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp, root = mutated_copy()
        path = root / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return temp, root

    def test_hollow_removed_clause_fails(self) -> None:
        temp, root = self.mutate_skill("## C4. Repeated failure escalates", "## dropped. Repeated failure escalates")
        self.addCleanup(temp.cleanup)
        errors = validate(root)
        # the kernel/clause count tie catches the drop even above the floor of 8
        self.assertTrue(
            any("kernel/clause count mismatch" in e or "at least 8 clauses" in e for e in errors),
            errors,
        )

    def test_hollow_removed_action_fails(self) -> None:
        temp, root = self.mutate_skill("- Action: the monitor consumes", "- Note: the monitor consumes")
        self.addCleanup(temp.cleanup)
        self.assertTrue(any("C1" in e and "Action" in e for e in validate(root)), validate(root))

    def test_hollow_unbound_evidence_fails(self) -> None:
        temp, root = self.mutate_skill("- evidence: poison-pill", "- evidence: unproven-story")
        self.addCleanup(temp.cleanup)
        errors = validate(root)
        self.assertTrue(any("unproven-story" in e for e in errors), errors)
        self.assertTrue(any("poison-pill" in e and "bound to no clause" in e for e in errors), errors)

    def test_hollow_receipt_without_refs_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "receipts.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["evidence"]["poison-pill"]["refs"] = []
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any("poison-pill" in e and "refs" in e for e in validate(root)), validate(root))

    def test_hollow_topology_removed_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        (root / "domain" / "machine-topology.json").unlink()
        self.assertTrue(any("machine-topology.json missing" in e for e in validate(root)), validate(root))

    def test_hollow_kernel_dropped_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "references" / "portable-supervision-kernel.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("- K9 ", text)
        path.write_text(text.replace("- K9 ", "- dropped ", 1), encoding="utf-8")
        self.assertTrue(any("kernel/clause count mismatch" in e for e in validate(root)), validate(root))

    def test_hollow_empty_host_ref_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "receipts.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["evidence"]["exit-residue"]["refs"] = ["host:"]
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any("exit-residue" in e and "refs" in e for e in validate(root)), validate(root))

    def test_hollow_provenance_removed_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("skills-shared", text)
        path.write_text(text.replace("skills-shared", "elsewhere"), encoding="utf-8")
        self.assertTrue(any("provenance" in e for e in validate(root)), validate(root))

    # --- campaign machinery: the judge keeps a case it must refuse, and waves land append-only ---

    def test_hollow_negative_control_dropped_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        rewrite_json(
            root / BEHAVIORAL,
            lambda d: d.__setitem__(
                "scenarios", [s for s in d["scenarios"] if s.get("control") != "negative"]
            ),
        )
        errors = validate(root)
        self.assertTrue(any("control:negative" in e for e in errors), errors)

    def test_hollow_negative_transcript_missing_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        case = next(
            s
            for s in json.loads((root / BEHAVIORAL).read_text(encoding="utf-8"))["scenarios"]
            if s.get("control") == "negative"
        )
        (root / case["transcript"]).unlink()
        errors = validate(root)
        self.assertTrue(any("transcript fixture missing" in e for e in errors), errors)

    def test_hollow_negative_expected_verdict_softened_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)

        def soften(data: dict) -> None:
            for scenario in data["scenarios"]:
                if scenario.get("control") == "negative":
                    scenario["expected_verdict"] = "unscored"

        rewrite_json(root / BEHAVIORAL, soften)
        errors = validate(root)
        self.assertTrue(any("expected_verdict" in e for e in errors), errors)

    def test_hollow_ledger_entry_removed_fails(self) -> None:
        """Appends stay green; deleting a prior entry cuts the chain even when
        the tail digest is repaired."""
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        path = root / LEDGER
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data["entries"]
        appended = dict(entries[-1], wave="synthetic-append", prev_sha256=entry_digest(entries[-1]))
        entries.append(appended)
        data["head_sha256"] = entry_digest(appended)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.assertEqual(validate(root), [], "appending a wave must stay green")

        del entries[0]
        data["head_sha256"] = entry_digest(entries[-1])
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        errors = validate(root)
        self.assertTrue(any("append-only chain" in e for e in errors), errors)

    def test_hollow_ledger_tail_rewritten_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        rewrite_json(root / LEDGER, lambda d: d["entries"][-1]["gaps"].append("laundered"))
        errors = validate(root)
        self.assertTrue(any("head_sha256" in e for e in errors), errors)

    def test_hollow_ledger_key_missing_fails(self) -> None:
        temp, root = mutated_copy()
        self.addCleanup(temp.cleanup)
        rewrite_json(root / LEDGER, lambda d: d["entries"][-1].pop("prompt_improvements"))
        errors = validate(root)
        self.assertTrue(any("prompt_improvements" in e for e in errors), errors)

    def test_ledger_producer_refuses_dropped_or_rewritten_entry(self) -> None:
        """The hash chain alone stays self-consistent even if gen_ledger.py is
        re-run against a shortened or edited ENTRIES list, so the producer's
        own prefix diff is what has to catch it."""
        committed = json.loads((SKILL_ROOT / LEDGER).read_text(encoding="utf-8"))["entries"]

        appended = dict(committed[-1], wave="synthetic-append", prev_sha256=entry_digest(committed[-1]))
        self.assertEqual(check_prefix_preserved(committed, committed + [appended]), [])

        self.assertTrue(
            any("shrink" in e for e in check_prefix_preserved(committed, committed[:-1])),
        )

        # same length as committed so the byte-compare branch is exercised
        # regardless of how many waves the ledger has accumulated
        rewritten = [dict(committed[0], gaps=["laundered"])] + committed[1:]
        errors = check_prefix_preserved(committed, rewritten)
        self.assertTrue(any("laundering" in e for e in errors), errors)


class ABCampaign(unittest.TestCase):
    """The A/B control-arm campaign's gates.

    The invariant the blindness gate exists to enforce is: NO JUDGE INPUT
    CARRIES A HARNESS-AUTHORED LABEL OF WHICH ARM PRODUCED IT. It does not
    claim the arm is unguessable - an actor holding the manual can cite it, and
    that residual is counted (SOFT_LEAK) rather than asserted away.
    """

    def staged_runs(self) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temp = tempfile.TemporaryDirectory(prefix="slg-ab-")
        runs = Path(temp.name) / "runs"
        shutil.copytree(AB / "runs", runs)
        return temp, runs, Path(temp.name) / "judge-inputs"

    def test_planted_arm_leak_reds_the_blindness_scan(self) -> None:
        """The gate's own negative control: plant the leak, watch it refuse."""
        temp, runs, dest = self.staged_runs()
        self.addCleanup(temp.cleanup)
        self.assertEqual(ab_campaign.build_judge_inputs(runs, dest), 0, "clean runs must build")
        shutil.rmtree(dest)

        leak = (AB / "fixtures" / "arm-leak-planted" / "calls.log").read_text(encoding="utf-8")
        victim = sorted(p for p in runs.iterdir() if p.is_dir())[0] / "calls.log"
        victim.write_text(victim.read_text(encoding="utf-8") + leak, encoding="utf-8")
        self.assertEqual(ab_campaign.build_judge_inputs(runs, dest), 1)
        self.assertFalse(dest.exists(), "a refused build must write nothing")

    def test_committed_judge_inputs_carry_no_arm_label(self) -> None:
        self.assertEqual(ab_campaign.scan_tree(AB / "judge-inputs", ab_campaign.HARD_LEAK), [])

    def test_manual_never_reaches_runs_or_judge_inputs(self) -> None:
        for root in (AB / "runs", AB / "judge-inputs"):
            stray = [p.as_posix() for p in root.rglob(ab_campaign.MANUAL_NAME)]
            self.assertEqual(stray, [], f"the treatment leaked into {root.name}")

    def test_manual_carries_every_admitted_clause(self) -> None:
        """The arm-with bytes ARE the admitted bytes: a clause that lands
        outside the shipped slice would silently stop being under test."""
        body = ab_campaign.manual_body()
        skill_md = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(body, skill_md)
        for clause in re.findall(r"^## (C\d+)\. ", skill_md, re.M):
            self.assertIn(f"## {clause}. ", body, f"{clause} is not in the arm-with manual")

    def test_committed_receipt_still_matches_its_producer(self) -> None:
        """Hand-editing the receipt is laundering; this reds when it happens."""
        spec = ab_campaign.load(ab_campaign.SPEC_PATH)
        recomputed = ab_campaign.compute_scores(
            spec,
            ab_campaign.load(ab_campaign.ASSIGNMENT_PATH),
            ab_campaign.load(ab_campaign.JUDGMENTS_PATH),
            ab_campaign.collect_oracles(spec, AB / "judge-inputs"),
        )
        committed = ab_campaign.load(ab_campaign.RECEIPT_PATH)
        for key in ("arm_scores", "delta", "tie", "oracle_arm_scores", "judge_oracle_agreement"):
            self.assertEqual(committed[key], recomputed[key], key)

    def test_selftest_passes(self) -> None:
        self.assertEqual(ab_campaign.selftest(), 0)


if __name__ == "__main__":
    unittest.main()
