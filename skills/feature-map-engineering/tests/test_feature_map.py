from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from feature_map import (  # noqa: E402
    ContractError,
    coverage_diff,
    validate_feature_map,
    validate_verification_plan,
)


class FeatureMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = SKILL_ROOT / "fixtures" / "valid"
        cls.feature_map = json.loads(
            (fixture / "feature-map.json").read_text(encoding="utf-8")
        )
        cls.plan = json.loads(
            (fixture / "verification-plan.json").read_text(encoding="utf-8")
        )

    def assert_contract_error(self, expected: str, fn) -> None:
        with self.assertRaises(ContractError) as caught:
            fn()
        self.assertTrue(
            any(code.startswith(expected) for code in caught.exception.codes),
            caught.exception.codes,
        )

    def test_positive_complete_feature_proof(self) -> None:
        summary = validate_verification_plan(
            copy.deepcopy(self.feature_map), copy.deepcopy(self.plan)
        )
        self.assertEqual("VERIFIED", summary["verdict"])
        self.assertEqual(["cancelled", "completed"], summary["verified_terminals"])
        self.assertEqual(2, summary["journey_count"])

    def test_missing_terminal_oracle_fails(self) -> None:
        feature_map = copy.deepcopy(self.feature_map)
        feature_map["observables"] = [
            item
            for item in feature_map["observables"]
            if item["state"] != "cancelled"
        ]
        self.assert_contract_error(
            "TERMINAL_WITHOUT_ORACLE",
            lambda: validate_feature_map(feature_map),
        )

    def test_static_only_false_proof_fails(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["journeys"][0]["evidence"] = [
            {
                "kind": "static-inspection",
                "boundary": "internal",
                "assertion": "the handler appears to set completed",
            }
        ]
        self.assert_contract_error(
            "STATIC_ONLY_VERIFICATION",
            lambda: validate_verification_plan(
                copy.deepcopy(self.feature_map), plan
            ),
        )

    def test_skip_without_blocker_fails(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["journeys"] = [
            journey
            for journey in plan["journeys"]
            if journey["expected_terminal"] != "cancelled"
        ]
        plan["skips"] = [
            {
                "id": "cancel-unavailable",
                "feature": "workflow-retry",
                "terminal": "cancelled",
                "path": "CLI cancel route",
                "nearest_reachable_path": "API success route",
                "residual_uncertainty": "cancel behavior is unobserved",
            }
        ]
        self.assert_contract_error(
            "SKIP_WITHOUT_BLOCKER",
            lambda: validate_verification_plan(
                copy.deepcopy(self.feature_map), plan
            ),
        )

    def test_changed_feature_without_proof_fails(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["journeys"] = []
        plan["skips"] = []
        self.assert_contract_error(
            "CHANGED_FEATURE_WITHOUT_PROOF",
            lambda: validate_verification_plan(
                copy.deepcopy(self.feature_map), plan
            ),
        )

    def test_invalid_transition_chain_fails(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["journeys"][0]["transition_ids"] = ["complete"]
        self.assert_contract_error(
            "JOURNEY_CHAIN_INVALID",
            lambda: validate_verification_plan(
                copy.deepcopy(self.feature_map), plan
            ),
        )

    def test_persistence_evidence_missing_fails(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["journeys"][0]["evidence"] = [
            {
                "kind": "observable",
                "boundary": "external",
                "assertion": "terminal response exposes completed",
            }
        ]
        self.assert_contract_error(
            "PERSISTENCE_PROOF_MISSING",
            lambda: validate_verification_plan(
                copy.deepcopy(self.feature_map), plan
            ),
        )

    def test_coverage_diff_detects_changed_edge(self) -> None:
        new_map = copy.deepcopy(self.feature_map)
        new_map["transitions"][0]["action"] = "request retry"
        result = coverage_diff(copy.deepcopy(self.feature_map), new_map)
        self.assertTrue(result["requires_reverification"])
        self.assertEqual(["retry"], result["transitions"]["changed"])


if __name__ == "__main__":
    unittest.main()
