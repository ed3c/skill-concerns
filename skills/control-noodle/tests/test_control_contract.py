from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from control_contract import ContractError, validate_bundle  # noqa: E402


class ControlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = SKILL_ROOT / "fixtures" / "valid"

        def load(root: Path, name: str):
            return json.loads((root / name).read_text(encoding="utf-8"))

        domain = SKILL_ROOT / "domain"
        cls.composition = load(domain, "composition.json")
        cls.feature_map = load(domain, "feature-map.json")
        cls.code_map = load(domain, "code-map.json")
        cls.mapping = load(domain, "feature-code-map.json")
        cls.adapter = load(domain, "domain-adapter.json")
        cls.change_set = load(fixture, "change-set.json")
        cls.plan = load(fixture, "verification-plan.json")
        cls.procedure_admission = load(fixture, "procedure-admission.json")
        cls.source_lock = load(
            SKILL_ROOT.parents[1] / "intake" / "control-noodle", "source-lock.json"
        )

    def validate(self, **overrides):
        values = {
            "composition": copy.deepcopy(self.composition),
            "feature_map": copy.deepcopy(self.feature_map),
            "code_map": copy.deepcopy(self.code_map),
            "mapping": copy.deepcopy(self.mapping),
            "adapter": copy.deepcopy(self.adapter),
            "change_set": copy.deepcopy(self.change_set),
            "plan": copy.deepcopy(self.plan),
            "procedure_admission": copy.deepcopy(self.procedure_admission),
            "source_lock": copy.deepcopy(self.source_lock),
        }
        values.update(overrides)
        return validate_bundle(**values)

    def assert_contract_error(self, expected: str, **overrides) -> None:
        with self.assertRaises(ContractError) as caught:
            self.validate(**overrides)
        self.assertTrue(
            any(code.startswith(expected) for code in caught.exception.codes),
            caught.exception.codes,
        )

    def test_positive_composed_control_bundle(self) -> None:
        summary = self.validate()
        self.assertEqual("BLOCKED", summary["verdict"])
        self.assertEqual(
            ["handoff-to-awaiting-land", "provider-landed-to-reconciled"],
            summary["affected_feature_edges"],
        )
        self.assertEqual(["issue-to-reconcile"], summary["required_journeys"])

    def test_stale_domain_source_commit_fails(self) -> None:
        change_set = copy.deepcopy(self.change_set)
        change_set["source_commit"] = "0" * 40
        self.assert_contract_error("SOURCE_COMMIT_DRIFT", change_set=change_set)

    def test_source_lock_domain_drift_fails(self) -> None:
        source_lock = copy.deepcopy(self.source_lock)
        source_lock["method_references"][0]["commit"] = "0" * 40
        self.assert_contract_error("SOURCE_LOCK_DOMAIN_DRIFT", source_lock=source_lock)

    def test_changed_code_node_without_feature_mapping_fails(self) -> None:
        change_set = copy.deepcopy(self.change_set)
        change_set["changed_code_nodes"] = ["issue-contract-parser"]
        self.assert_contract_error("CHANGED_CODE_NODE_UNMAPPED", change_set=change_set)

    def test_mapping_to_unknown_code_node_fails(self) -> None:
        mapping = copy.deepcopy(self.mapping)
        mapping["feature_edges"][0]["code_nodes"].append("missing-node")
        self.assert_contract_error("MAPPING_CODE_NODE_UNKNOWN", mapping=mapping)

    def test_mapping_to_unknown_transition_fails(self) -> None:
        mapping = copy.deepcopy(self.mapping)
        mapping["feature_edges"][0]["transition_id"] = "invented-transition"
        self.assert_contract_error("MAPPING_TRANSITION_UNKNOWN", mapping=mapping)

    def test_required_journey_cannot_be_omitted(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["journeys"] = []
        self.assert_contract_error("REQUIRED_JOURNEY_MISSING", plan=plan)

    def test_static_only_evidence_cannot_verify(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["journeys"][0]["verdict"] = "VERIFIED"
        plan["journeys"][0]["evidence"] = [
            {
                "kind": "static-inspection",
                "boundary": "internal",
                "assertion": "the implementation appears connected",
            }
        ]
        self.assert_contract_error("STATIC_ONLY_VERIFICATION", plan=plan)

    def test_unavailable_runtime_cannot_be_promoted(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["environment"]["runtime_available"] = False
        plan["journeys"][0]["verdict"] = "VERIFIED"
        self.assert_contract_error("UNAVAILABLE_RUNTIME_PROMOTED", plan=plan)

    def test_unexercised_live_runtime_cannot_be_promoted(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["journeys"][0]["verdict"] = "VERIFIED"
        plan["journeys"][0]["evidence"] = [
            {
                "kind": "observable",
                "boundary": "external",
                "assertion": "a claimed provider receipt",
            },
            {
                "kind": "observable",
                "boundary": "persisted",
                "assertion": "a claimed process restart readback",
            },
        ]
        self.assert_contract_error("LIVE_RUNTIME_NOT_EXERCISED_PROMOTED", plan=plan)

    def test_stale_procedure_dependency_fails(self) -> None:
        procedure_admission = copy.deepcopy(self.procedure_admission)
        procedure_admission["skill_tree_sha256"] = "f" * 64
        self.assert_contract_error(
            "PROCEDURE_SUBJECT_DRIFT", procedure_admission=procedure_admission
        )

    def test_mutable_upstream_path_in_adapter_fails(self) -> None:
        adapter = copy.deepcopy(self.adapter)
        adapter["drivers"].append("/Users/neon/noodles/noodles.py")
        self.assert_contract_error("ADAPTER_MUTABLE_PATH", adapter=adapter)


if __name__ == "__main__":
    unittest.main()
