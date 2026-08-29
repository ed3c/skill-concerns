"""Validate a composed control Skill and compile code changes into proof journeys.

The module consumes already-frozen domain facts. It never starts a runtime,
mutates a provider, or discovers mutable upstream state.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any


PROCEDURE_SCRIPTS = (
    Path(__file__).resolve().parents[2] / "feature-map-engineering" / "scripts"
)
sys.path.insert(0, str(PROCEDURE_SCRIPTS))

from feature_map import (  # noqa: E402
    ContractError,
    validate_feature_map,
    validate_verification_plan,
)


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_LEVELS = [
    "L0_SOURCE_FREEZE",
    "L1_STRUCTURAL",
    "L2_EXECUTABLE_CONTRACT",
    "L3_HERMETIC",
    "L4_MATCHED_LIVE_RUNTIME",
    "L5_DELIVERY_AND_PRODUCTION",
]


def _string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _objects(value: Any, label: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{label}_NOT_LIST")
        return []
    result: list[dict[str, Any]] = []
    for position, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{label}_NOT_OBJECT:{position}")
            continue
        result.append(item)
    return result


def _index(
    values: list[dict[str, Any]], key: str, label: str, errors: list[str]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for position, item in enumerate(values):
        identity = item.get(key)
        if not _string(identity):
            errors.append(f"{label}_ID_MISSING:{position}")
            continue
        identity = identity.strip()
        if identity in result:
            errors.append(f"{label}_ID_DUPLICATE:{identity}")
            continue
        result[identity] = item
    return result


def _validate_composition(
    composition: Any, procedure_admission: Any, errors: list[str]
) -> str:
    if not isinstance(composition, dict):
        errors.append("COMPOSITION_NOT_OBJECT")
        return ""
    if composition.get("schema_version") != 1:
        errors.append("COMPOSITION_SCHEMA_VERSION")
    if composition.get("procedure_skill") != "feature-map-engineering":
        errors.append("PROCEDURE_SKILL_INVALID")
    expected_tree = composition.get("procedure_tree_sha256")
    if not isinstance(expected_tree, str) or not HEX64.fullmatch(expected_tree):
        errors.append("PROCEDURE_SUBJECT_INVALID")

    if not isinstance(procedure_admission, dict):
        errors.append("PROCEDURE_ADMISSION_NOT_OBJECT")
    else:
        if procedure_admission.get("skill") != composition.get("procedure_skill"):
            errors.append("PROCEDURE_ADMISSION_SKILL_DRIFT")
        if procedure_admission.get("skill_tree_sha256") != expected_tree:
            errors.append("PROCEDURE_SUBJECT_DRIFT")
        ceiling = procedure_admission.get("evidence_ceiling")
        if (
            ceiling not in EVIDENCE_LEVELS
            or EVIDENCE_LEVELS.index(ceiling)
            < EVIDENCE_LEVELS.index("L3_HERMETIC")
        ):
            errors.append("PROCEDURE_EVIDENCE_BELOW_L3")

    subject = composition.get("domain_subject")
    if not isinstance(subject, dict):
        errors.append("DOMAIN_SUBJECT_NOT_OBJECT")
        return ""
    if not _string(subject.get("repository")):
        errors.append("DOMAIN_REPOSITORY_MISSING")
    commit = subject.get("commit")
    if not isinstance(commit, str) or not HEX40.fullmatch(commit):
        errors.append("DOMAIN_COMMIT_INVALID")
        return ""
    return commit


def _validate_code_map(
    code_map: Any, source_commit: str, errors: list[str]
) -> dict[str, dict[str, Any]]:
    if not isinstance(code_map, dict):
        errors.append("CODE_MAP_NOT_OBJECT")
        return {}
    if code_map.get("schema_version") != 1:
        errors.append("CODE_MAP_SCHEMA_VERSION")
    subject = code_map.get("subject")
    if not isinstance(subject, dict) or subject.get("commit") != source_commit:
        errors.append("SOURCE_COMMIT_DRIFT:code-map")
    nodes = _index(
        _objects(code_map.get("nodes"), "CODE_NODES", errors),
        "id",
        "CODE_NODE",
        errors,
    )
    for node_id, node in nodes.items():
        if node.get("kind") not in {
            "entrypoint",
            "module",
            "function",
            "state-store",
            "provider-boundary",
            "control-boundary",
        }:
            errors.append(f"CODE_NODE_KIND_INVALID:{node_id}")
        if not _string(node.get("path")):
            errors.append(f"CODE_NODE_PATH_MISSING:{node_id}")
        if not _string(node.get("symbol")):
            errors.append(f"CODE_NODE_SYMBOL_MISSING:{node_id}")

    edges = _index(
        _objects(code_map.get("edges"), "CODE_EDGES", errors),
        "id",
        "CODE_EDGE",
        errors,
    )
    for edge_id, edge in edges.items():
        if edge.get("from") not in nodes:
            errors.append(f"CODE_EDGE_SOURCE_UNKNOWN:{edge_id}:{edge.get('from')}")
        if edge.get("to") not in nodes:
            errors.append(f"CODE_EDGE_TARGET_UNKNOWN:{edge_id}:{edge.get('to')}")
        if not _string(edge.get("relation")):
            errors.append(f"CODE_EDGE_RELATION_MISSING:{edge_id}")
    return nodes


def _validate_source_lock(
    source_lock: Any,
    repository: str,
    source_commit: str,
    code_index: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if not isinstance(source_lock, dict):
        errors.append("SOURCE_LOCK_NOT_OBJECT")
        return
    references = source_lock.get("method_references")
    if not isinstance(references, list) or not references:
        errors.append("SOURCE_LOCK_METHOD_REFERENCES_EMPTY")
        return
    referenced_paths: set[str] = set()
    for position, reference in enumerate(references):
        if not isinstance(reference, dict):
            errors.append(f"SOURCE_LOCK_METHOD_REFERENCE_NOT_OBJECT:{position}")
            continue
        if (
            reference.get("repository") != repository
            or reference.get("commit") != source_commit
        ):
            errors.append(f"SOURCE_LOCK_DOMAIN_DRIFT:{position}")
        path = reference.get("path")
        blob = reference.get("blob_sha")
        if not _string(path):
            errors.append(f"SOURCE_LOCK_METHOD_PATH_MISSING:{position}")
        else:
            referenced_paths.add(path)
        if not isinstance(blob, str) or not HEX40.fullmatch(blob):
            errors.append(f"SOURCE_LOCK_METHOD_BLOB_INVALID:{position}")

    required_paths = {
        node.get("path")
        for node in code_index.values()
        if _string(node.get("path")) and not node["path"].startswith(".noodle/")
    }
    for path in sorted(required_paths - referenced_paths):
        errors.append(f"CODE_MAP_SOURCE_UNFROZEN:{path}")


def _validate_adapter(adapter: Any, errors: list[str]) -> None:
    if not isinstance(adapter, dict):
        errors.append("DOMAIN_ADAPTER_NOT_OBJECT")
        return
    if adapter.get("schema_version") != 1:
        errors.append("DOMAIN_ADAPTER_SCHEMA_VERSION")
    required = {
        "feature_map_root",
        "drivers",
        "selectors",
        "commands",
        "assertion_helpers",
        "runtime_setup",
        "feature_flags",
        "external_boundaries",
        "proof_artifacts",
    }
    for key in sorted(required):
        value = adapter.get(key)
        if key == "feature_map_root":
            if not _string(value):
                errors.append("ADAPTER_FEATURE_MAP_ROOT_MISSING")
            continue
        if not isinstance(value, list) or any(not _string(item) for item in value):
            errors.append(f"ADAPTER_FIELD_INVALID:{key}")
            continue
        for item in value:
            candidate = item.strip()
            if candidate.startswith(("/", "~/")) or "/.noodle/providers/" in candidate:
                errors.append(f"ADAPTER_MUTABLE_PATH:{key}:{candidate}")


def _validate_mapping(
    mapping: Any,
    source_commit: str,
    feature: str,
    transition_ids: set[str],
    code_nodes: set[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(mapping, dict):
        errors.append("FEATURE_CODE_MAP_NOT_OBJECT")
        return []
    if mapping.get("schema_version") != 1:
        errors.append("FEATURE_CODE_MAP_SCHEMA_VERSION")
    if mapping.get("source_commit") != source_commit:
        errors.append("SOURCE_COMMIT_DRIFT:feature-code-map")
    if mapping.get("feature") != feature:
        errors.append("MAPPING_FEATURE_DRIFT")

    entries = _objects(mapping.get("feature_edges"), "FEATURE_EDGES", errors)
    seen: set[str] = set()
    for position, entry in enumerate(entries):
        transition = entry.get("transition_id")
        if not _string(transition):
            errors.append(f"MAPPING_TRANSITION_MISSING:{position}")
            continue
        if transition in seen:
            errors.append(f"MAPPING_TRANSITION_DUPLICATE:{transition}")
        seen.add(transition)
        if transition not in transition_ids:
            errors.append(f"MAPPING_TRANSITION_UNKNOWN:{transition}")
        mapped_nodes = entry.get("code_nodes")
        if not isinstance(mapped_nodes, list) or not mapped_nodes:
            errors.append(f"MAPPING_CODE_NODES_EMPTY:{transition}")
            mapped_nodes = []
        for node in mapped_nodes:
            if node not in code_nodes:
                errors.append(f"MAPPING_CODE_NODE_UNKNOWN:{transition}:{node}")
        journeys = entry.get("required_journeys")
        if not isinstance(journeys, list) or not journeys or any(
            not _string(item) for item in journeys
        ):
            errors.append(f"MAPPING_REQUIRED_JOURNEYS_INVALID:{transition}")
    return entries


def _compile_change_set(
    change_set: Any,
    source_commit: str,
    code_nodes: set[str],
    mappings: list[dict[str, Any]],
    errors: list[str],
) -> tuple[list[str], list[str]]:
    if not isinstance(change_set, dict):
        errors.append("CHANGE_SET_NOT_OBJECT")
        return [], []
    if change_set.get("schema_version") != 1:
        errors.append("CHANGE_SET_SCHEMA_VERSION")
    if change_set.get("source_commit") != source_commit:
        errors.append("SOURCE_COMMIT_DRIFT:change-set")
    changed = change_set.get("changed_code_nodes")
    if (
        not isinstance(changed, list)
        or not changed
        or any(not _string(item) for item in changed)
    ):
        errors.append("CHANGED_CODE_NODES_INVALID")
        return [], []

    affected: set[str] = set()
    journeys: set[str] = set()
    for node in changed:
        if node not in code_nodes:
            errors.append(f"CHANGED_CODE_NODE_UNKNOWN:{node}")
            continue
        matches = [entry for entry in mappings if node in entry.get("code_nodes", [])]
        if not matches:
            errors.append(f"CHANGED_CODE_NODE_UNMAPPED:{node}")
            continue
        for entry in matches:
            transition = entry.get("transition_id")
            if _string(transition):
                affected.add(transition)
            for journey in entry.get("required_journeys", []):
                if _string(journey):
                    journeys.add(journey)
    return sorted(affected), sorted(journeys)


def validate_bundle(
    *,
    composition: Any,
    feature_map: Any,
    code_map: Any,
    mapping: Any,
    adapter: Any,
    change_set: Any,
    plan: Any,
    procedure_admission: Any,
    source_lock: Any,
) -> dict[str, Any]:
    """Validate all composed subjects and compile the required proof denominator."""

    errors: list[str] = []
    source_commit = _validate_composition(composition, procedure_admission, errors)
    domain_subject = (
        composition.get("domain_subject", {}) if isinstance(composition, dict) else {}
    )

    try:
        feature_index = validate_feature_map(feature_map)
    except ContractError as exc:
        errors.extend(exc.codes)
        feature_index = None

    code_index = _validate_code_map(code_map, source_commit, errors)
    _validate_source_lock(
        source_lock,
        domain_subject.get("repository", ""),
        source_commit,
        code_index,
        errors,
    )
    _validate_adapter(adapter, errors)
    mappings = _validate_mapping(
        mapping,
        source_commit,
        feature_index.feature if feature_index else "",
        set(feature_index.transitions) if feature_index else set(),
        set(code_index),
        errors,
    )
    affected_edges, required_journeys = _compile_change_set(
        change_set, source_commit, set(code_index), mappings, errors
    )

    plan_journeys = set()
    if isinstance(plan, dict) and isinstance(plan.get("journeys"), list):
        plan_journeys = {
            item.get("id")
            for item in plan["journeys"]
            if isinstance(item, dict) and _string(item.get("id"))
        }
    for journey in required_journeys:
        if journey not in plan_journeys:
            errors.append(f"REQUIRED_JOURNEY_MISSING:{journey}")

    if isinstance(plan, dict):
        environment = plan.get("environment")
        verified_requested = any(
            isinstance(item, dict) and item.get("verdict") == "VERIFIED"
            for item in plan.get("journeys", [])
        )
        if (
            isinstance(environment, dict)
            and environment.get("runtime_available") is False
            and verified_requested
        ):
            errors.append("UNAVAILABLE_RUNTIME_PROMOTED")
        if (
            isinstance(environment, dict)
            and environment.get("live_runtime_exercised") is False
            and verified_requested
        ):
            errors.append("LIVE_RUNTIME_NOT_EXERCISED_PROMOTED")

    if feature_index is not None:
        try:
            proof_summary = validate_verification_plan(feature_map, plan)
        except ContractError as exc:
            errors.extend(exc.codes)
            proof_summary = None
    else:
        proof_summary = None

    if errors:
        raise ContractError(errors)
    assert proof_summary is not None
    return {
        **proof_summary,
        "source_commit": source_commit,
        "affected_feature_edges": affected_edges,
        "required_journeys": required_journeys,
        "evidence_ceiling": "L3_HERMETIC",
        "not_claimed": [
            "L4_MATCHED_LIVE_RUNTIME",
            "L5_DELIVERY_AND_PRODUCTION",
        ],
    }
