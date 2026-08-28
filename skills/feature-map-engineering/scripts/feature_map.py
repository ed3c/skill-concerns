"""Executable FeatureMap IR and proof-plan meta-assertions.

Standard-library only. This module validates generic behavioral topology and
proof semantics; it intentionally knows nothing about a product driver.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


HIGH_EVIDENCE_BOUNDARIES = {"production-equivalent", "external", "persisted"}
ALLOWED_EVIDENCE_KINDS = {
    "observable",
    "trace",
    "integration-test",
    "unit-test",
    "static-inspection",
}
ALLOWED_VERDICTS = {
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "BLOCKED",
    "NOT_VERIFIED",
}


class ContractError(ValueError):
    """Raised when one or more deterministic contract rules fail."""

    def __init__(self, codes: Iterable[str]):
        self.codes = tuple(dict.fromkeys(codes))
        super().__init__("\n".join(self.codes))


@dataclass(frozen=True)
class FeatureIndex:
    feature: str
    states: dict[str, dict[str, Any]]
    entry_points: dict[str, dict[str, Any]]
    transitions: dict[str, dict[str, Any]]
    terminals: dict[str, dict[str, Any]]
    observables: dict[str, dict[str, Any]]
    persistence_required: bool


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_nonempty_string(
    obj: dict[str, Any], key: str, errors: list[str], code: str
) -> str:
    value = obj.get(key)
    if not _is_nonempty_string(value):
        errors.append(code)
        return ""
    return value.strip()


def _require_list(
    obj: dict[str, Any], key: str, errors: list[str], code: str
) -> list[Any]:
    value = obj.get(key)
    if not isinstance(value, list):
        errors.append(code)
        return []
    return value


def _index_objects(
    values: list[Any], key: str, label: str, errors: list[str]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for position, value in enumerate(values):
        if not isinstance(value, dict):
            errors.append(f"{label.upper()}_NOT_OBJECT:{position}")
            continue
        identity = value.get(key)
        if not _is_nonempty_string(identity):
            errors.append(f"{label.upper()}_ID_MISSING:{position}")
            continue
        identity = identity.strip()
        if identity in result:
            errors.append(f"{label.upper()}_ID_DUPLICATE:{identity}")
            continue
        result[identity] = value
    return result


def validate_feature_map(data: Any) -> FeatureIndex:
    errors: list[str] = []
    if not isinstance(data, dict):
        raise ContractError(["FEATURE_MAP_NOT_OBJECT"])

    if data.get("schema_version") != 1:
        errors.append("FEATURE_MAP_SCHEMA_VERSION")

    feature = _require_nonempty_string(
        data, "feature", errors, "FEATURE_IDENTITY_MISSING"
    )
    _require_nonempty_string(data, "actor", errors, "FEATURE_ACTOR_MISSING")
    _require_nonempty_string(data, "intent", errors, "FEATURE_INTENT_MISSING")

    states = _index_objects(
        _require_list(data, "states", errors, "STATES_NOT_LIST"),
        "id",
        "state",
        errors,
    )
    entry_points = _index_objects(
        _require_list(data, "entry_points", errors, "ENTRY_POINTS_NOT_LIST"),
        "id",
        "entry_point",
        errors,
    )
    transitions = _index_objects(
        _require_list(data, "transitions", errors, "TRANSITIONS_NOT_LIST"),
        "id",
        "transition",
        errors,
    )
    observables = _index_objects(
        _require_list(data, "observables", errors, "OBSERVABLES_NOT_LIST"),
        "id",
        "observable",
        errors,
    )

    terminal_values = _require_list(
        data, "terminal_outcomes", errors, "TERMINALS_NOT_LIST"
    )
    terminals = _index_objects(terminal_values, "state", "terminal", errors)

    if not states:
        errors.append("STATES_EMPTY")
    if not entry_points:
        errors.append("ENTRY_POINTS_EMPTY")
    if not terminals:
        errors.append("TERMINALS_EMPTY")
    if not observables:
        errors.append("OBSERVABLES_EMPTY")

    for entry_id, entry in entry_points.items():
        state = entry.get("state")
        if state not in states:
            errors.append(f"ENTRY_POINT_STATE_UNKNOWN:{entry_id}:{state}")
        if not _is_nonempty_string(entry.get("description")):
            errors.append(f"ENTRY_POINT_DESCRIPTION_MISSING:{entry_id}")

    for state_id, state in states.items():
        if not _is_nonempty_string(state.get("description")):
            errors.append(f"STATE_DESCRIPTION_MISSING:{state_id}")

    for transition_id, transition in transitions.items():
        source = transition.get("from")
        target = transition.get("to")
        if source not in states:
            errors.append(f"TRANSITION_SOURCE_UNKNOWN:{transition_id}:{source}")
        if target not in states:
            errors.append(f"TRANSITION_TARGET_UNKNOWN:{transition_id}:{target}")
        if not _is_nonempty_string(transition.get("action")):
            errors.append(f"TRANSITION_ACTION_MISSING:{transition_id}")
        if not isinstance(transition.get("reachable"), bool):
            errors.append(f"TRANSITION_REACHABILITY_MISSING:{transition_id}")

    allowed_outcomes = {
        "success",
        "cancel",
        "error",
        "empty",
        "timeout",
        "partial",
        "blocked",
    }
    for terminal_state, terminal in terminals.items():
        if terminal_state not in states:
            errors.append(f"TERMINAL_STATE_UNKNOWN:{terminal_state}")
        if terminal.get("outcome") not in allowed_outcomes:
            errors.append(f"TERMINAL_OUTCOME_INVALID:{terminal_state}")
        if not isinstance(terminal.get("reachable"), bool):
            errors.append(f"TERMINAL_REACHABILITY_MISSING:{terminal_state}")

    for observable_id, observable in observables.items():
        state = observable.get("state")
        if state not in states:
            errors.append(f"OBSERVABLE_STATE_UNKNOWN:{observable_id}:{state}")
        kind = observable.get("kind")
        boundary = observable.get("boundary")
        if kind not in ALLOWED_EVIDENCE_KINDS:
            errors.append(f"OBSERVABLE_KIND_INVALID:{observable_id}")
        if boundary not in {
            "production-equivalent",
            "external",
            "persisted",
            "internal",
            "test-only",
        }:
            errors.append(f"OBSERVABLE_BOUNDARY_INVALID:{observable_id}")
        if not _is_nonempty_string(observable.get("assertion")):
            errors.append(f"OBSERVABLE_ASSERTION_MISSING:{observable_id}")

    variants = data.get("variants")
    if not isinstance(variants, list) or any(
        not _is_nonempty_string(item) for item in variants
    ):
        errors.append("VARIANTS_INVALID")
    elif len(set(variants)) != len(variants):
        errors.append("VARIANTS_DUPLICATE")

    persistence = data.get("persistence")
    persistence_required = False
    if not isinstance(persistence, dict):
        errors.append("PERSISTENCE_NOT_OBJECT")
    else:
        persistence_required = persistence.get("required") is True
        if not isinstance(persistence.get("required"), bool):
            errors.append("PERSISTENCE_REQUIRED_INVALID")
        boundary = persistence.get("boundary")
        if persistence_required and not _is_nonempty_string(boundary):
            errors.append("PERSISTENCE_BOUNDARY_MISSING")
        if not persistence_required and boundary is not None and not _is_nonempty_string(
            boundary
        ):
            errors.append("PERSISTENCE_BOUNDARY_INVALID")

    # A reachable terminal must have a production-boundary observable oracle.
    for terminal_state, terminal in terminals.items():
        if terminal.get("reachable") is not True:
            continue
        qualifying = [
            observable
            for observable in observables.values()
            if observable.get("state") == terminal_state
            and observable.get("kind") == "observable"
            and observable.get("boundary") in HIGH_EVIDENCE_BOUNDARIES
        ]
        if not qualifying:
            errors.append(f"TERMINAL_WITHOUT_ORACLE:{terminal_state}")

    if errors:
        raise ContractError(errors)

    return FeatureIndex(
        feature=feature,
        states=states,
        entry_points=entry_points,
        transitions=transitions,
        terminals=terminals,
        observables=observables,
        persistence_required=persistence_required,
    )


def validate_verification_plan(
    feature_map: dict[str, Any], plan: Any
) -> dict[str, Any]:
    index = validate_feature_map(feature_map)
    errors: list[str] = []

    if not isinstance(plan, dict):
        raise ContractError(["VERIFICATION_PLAN_NOT_OBJECT"])
    if plan.get("schema_version") != 1:
        errors.append("VERIFICATION_PLAN_SCHEMA_VERSION")
    _require_nonempty_string(plan, "revision", errors, "REVISION_MISSING")
    environment = plan.get("environment")
    if not isinstance(environment, dict) or not environment:
        errors.append("ENVIRONMENT_MISSING")

    changed_features = _require_list(
        plan, "changed_features", errors, "CHANGED_FEATURES_NOT_LIST"
    )
    if any(not _is_nonempty_string(item) for item in changed_features):
        errors.append("CHANGED_FEATURE_INVALID")
    if len(set(changed_features)) != len(changed_features):
        errors.append("CHANGED_FEATURE_DUPLICATE")
    if index.feature not in changed_features:
        errors.append(f"CHANGED_FEATURE_NOT_BOUND:{index.feature}")

    journeys_list = _require_list(plan, "journeys", errors, "JOURNEYS_NOT_LIST")
    journeys = _index_objects(journeys_list, "id", "journey", errors)
    skips_list = _require_list(plan, "skips", errors, "SKIPS_NOT_LIST")
    skips = _index_objects(skips_list, "id", "skip", errors)

    covered_features: set[str] = set()
    verified_terminals: set[str] = set()

    for journey_id, journey in journeys.items():
        feature = journey.get("feature")
        if feature != index.feature:
            errors.append(f"JOURNEY_FEATURE_MISMATCH:{journey_id}:{feature}")
        else:
            covered_features.add(feature)

        entry_id = journey.get("entry_point")
        entry = index.entry_points.get(entry_id)
        if entry is None:
            errors.append(f"JOURNEY_ENTRY_POINT_UNKNOWN:{journey_id}:{entry_id}")
            current_state = None
        else:
            current_state = entry.get("state")

        transition_ids = journey.get("transition_ids")
        if not isinstance(transition_ids, list):
            errors.append(f"JOURNEY_TRANSITIONS_NOT_LIST:{journey_id}")
            transition_ids = []
        if any(not _is_nonempty_string(item) for item in transition_ids):
            errors.append(f"JOURNEY_TRANSITION_ID_INVALID:{journey_id}")

        for transition_id in transition_ids:
            transition = index.transitions.get(transition_id)
            if transition is None:
                errors.append(
                    f"JOURNEY_TRANSITION_UNKNOWN:{journey_id}:{transition_id}"
                )
                continue
            if transition.get("reachable") is not True:
                errors.append(
                    f"JOURNEY_TRANSITION_UNREACHABLE:{journey_id}:{transition_id}"
                )
            if current_state is not None and transition.get("from") != current_state:
                errors.append(
                    f"JOURNEY_CHAIN_INVALID:{journey_id}:{current_state}:{transition_id}"
                )
            current_state = transition.get("to")

        expected_terminal = journey.get("expected_terminal")
        if expected_terminal not in index.terminals:
            errors.append(
                f"JOURNEY_TERMINAL_UNKNOWN:{journey_id}:{expected_terminal}"
            )
        if current_state != expected_terminal:
            errors.append(
                f"JOURNEY_TERMINAL_MISMATCH:{journey_id}:{current_state}:{expected_terminal}"
            )

        verdict = journey.get("verdict")
        if verdict not in ALLOWED_VERDICTS:
            errors.append(f"JOURNEY_VERDICT_INVALID:{journey_id}:{verdict}")

        evidence = journey.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"JOURNEY_EVIDENCE_NOT_LIST:{journey_id}")
            evidence = []

        for position, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(f"EVIDENCE_NOT_OBJECT:{journey_id}:{position}")
                continue
            kind = item.get("kind")
            boundary = item.get("boundary")
            if kind not in ALLOWED_EVIDENCE_KINDS:
                errors.append(f"EVIDENCE_KIND_INVALID:{journey_id}:{position}")
            if boundary not in {
                "production-equivalent",
                "external",
                "persisted",
                "internal",
                "test-only",
            }:
                errors.append(f"EVIDENCE_BOUNDARY_INVALID:{journey_id}:{position}")
            if not _is_nonempty_string(item.get("assertion")):
                errors.append(f"EVIDENCE_ASSERTION_MISSING:{journey_id}:{position}")

        if verdict == "VERIFIED":
            has_high_observable = any(
                isinstance(item, dict)
                and item.get("kind") == "observable"
                and item.get("boundary") in HIGH_EVIDENCE_BOUNDARIES
                and _is_nonempty_string(item.get("assertion"))
                for item in evidence
            )
            if not has_high_observable:
                errors.append(f"STATIC_ONLY_VERIFICATION:{journey_id}")
            if index.persistence_required:
                has_persisted = any(
                    isinstance(item, dict)
                    and item.get("kind") == "observable"
                    and item.get("boundary") == "persisted"
                    and _is_nonempty_string(item.get("assertion"))
                    for item in evidence
                )
                if not has_persisted:
                    errors.append(f"PERSISTENCE_PROOF_MISSING:{journey_id}")
            if expected_terminal in index.terminals:
                verified_terminals.add(expected_terminal)

    blocked_terminals: set[str] = set()
    for skip_id, skip in skips.items():
        feature = skip.get("feature")
        if feature != index.feature:
            errors.append(f"SKIP_FEATURE_MISMATCH:{skip_id}:{feature}")
        else:
            covered_features.add(feature)

        terminal = skip.get("terminal")
        if terminal not in index.terminals:
            errors.append(f"SKIP_TERMINAL_UNKNOWN:{skip_id}:{terminal}")
        else:
            blocked_terminals.add(terminal)

        path = skip.get("path")
        if not _is_nonempty_string(path):
            errors.append(f"SKIP_PATH_MISSING:{skip_id}")

        blocker = skip.get("blocker")
        if not isinstance(blocker, dict):
            errors.append(f"SKIP_WITHOUT_BLOCKER:{skip_id}")
        else:
            for key in ("type", "dependency", "detail"):
                if not _is_nonempty_string(blocker.get(key)):
                    errors.append(f"SKIP_BLOCKER_FIELD_MISSING:{skip_id}:{key}")

        if not _is_nonempty_string(skip.get("nearest_reachable_path")):
            errors.append(f"SKIP_NEAREST_PATH_MISSING:{skip_id}")
        if not _is_nonempty_string(skip.get("residual_uncertainty")):
            errors.append(f"SKIP_RESIDUAL_UNCERTAINTY_MISSING:{skip_id}")

    if index.feature not in covered_features:
        errors.append(f"CHANGED_FEATURE_WITHOUT_PROOF:{index.feature}")

    overlap = verified_terminals & blocked_terminals
    for terminal in sorted(overlap):
        errors.append(f"TERMINAL_BOTH_VERIFIED_AND_BLOCKED:{terminal}")

    for terminal_state, terminal in index.terminals.items():
        if terminal.get("reachable") is not True:
            continue
        if (
            terminal_state not in verified_terminals
            and terminal_state not in blocked_terminals
        ):
            errors.append(f"REACHABLE_TERMINAL_UNACCOUNTED:{terminal_state}")

    if errors:
        raise ContractError(errors)

    if blocked_terminals and verified_terminals:
        verdict = "PARTIALLY_VERIFIED"
    elif blocked_terminals:
        verdict = "BLOCKED"
    else:
        verdict = "VERIFIED"

    return {
        "feature": index.feature,
        "journey_count": len(journeys),
        "skip_count": len(skips),
        "verified_terminals": sorted(verified_terminals),
        "blocked_terminals": sorted(blocked_terminals),
        "verdict": verdict,
    }


def _by_identity(values: Any, identity_key: str) -> dict[str, Any]:
    if not isinstance(values, list):
        return {}
    result: dict[str, Any] = {}
    for value in values:
        if isinstance(value, dict) and _is_nonempty_string(value.get(identity_key)):
            result[value[identity_key]] = value
    return result


def _diff_index(
    old_values: Any, new_values: Any, identity_key: str
) -> dict[str, list[str]]:
    old = _by_identity(old_values, identity_key)
    new = _by_identity(new_values, identity_key)
    old_ids = set(old)
    new_ids = set(new)
    changed = sorted(
        identity for identity in old_ids & new_ids if old[identity] != new[identity]
    )
    return {
        "added": sorted(new_ids - old_ids),
        "removed": sorted(old_ids - new_ids),
        "changed": changed,
    }


def coverage_diff(old_map: dict[str, Any], new_map: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic behavioral topology changes."""

    old_index = validate_feature_map(old_map)
    new_index = validate_feature_map(new_map)

    top_level_changes = [
        key
        for key in ("feature", "actor", "intent", "variants", "persistence")
        if old_map.get(key) != new_map.get(key)
    ]
    diff = {
        "old_feature": old_index.feature,
        "new_feature": new_index.feature,
        "top_level_changed": top_level_changes,
        "entry_points": _diff_index(
            old_map.get("entry_points"), new_map.get("entry_points"), "id"
        ),
        "states": _diff_index(old_map.get("states"), new_map.get("states"), "id"),
        "transitions": _diff_index(
            old_map.get("transitions"), new_map.get("transitions"), "id"
        ),
        "terminal_outcomes": _diff_index(
            old_map.get("terminal_outcomes"),
            new_map.get("terminal_outcomes"),
            "state",
        ),
        "observables": _diff_index(
            old_map.get("observables"), new_map.get("observables"), "id"
        ),
    }
    diff["requires_reverification"] = bool(
        top_level_changes
        or any(
            section[change_type]
            for section_name, section in diff.items()
            if section_name
            in {
                "entry_points",
                "states",
                "transitions",
                "terminal_outcomes",
                "observables",
            }
            for change_type in ("added", "removed", "changed")
        )
    )
    return diff
