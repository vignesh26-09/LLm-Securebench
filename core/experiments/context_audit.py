"""Request-history integrity checks; never certify provider cache isolation."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Sequence

from core.experiments.models import ExperimentalCondition, ExperimentalObservation


def audit_request_histories(observations: Sequence[ExperimentalObservation]) -> dict[str, object]:
    groups: dict[tuple[str, str, str], list[ExperimentalObservation]] = defaultdict(list)
    issues: list[dict[str, str]] = []
    for item in observations:
        groups[(item.run_id, item.evaluation_case_id, item.conversation_id)].append(item)
        messages = item.ordered_messages
        if not messages or messages[-1].get("role") != ("assistant" if item.status.value == "completed" else "user"):
            issues.append({"observation_id": item.observation_id, "reason": "terminal_message_role_inconsistent"})
        ids = [message.get("message_id") for message in messages]
        if len(ids) != len(set(ids)):
            issues.append({"observation_id": item.observation_id, "reason": "duplicate_message_id"})
        reported_count = item.provider_metadata.get("message_count")
        if item.status.value == "completed" and isinstance(reported_count, int):
            expected_without_system = len(messages) - 1
            if reported_count not in {expected_without_system, expected_without_system + 1}:
                issues.append({"observation_id": item.observation_id, "reason": "provider_message_count_mismatch"})
    for group in groups.values():
        ordered = sorted(group, key=lambda item: item.turn_index)
        if len({item.turn_index for item in ordered}) != len(ordered):
            issues.append({"observation_id": ordered[0].observation_id,
                           "reason": "duplicate_turn_index_in_conversation"})
        for prior, later in zip(ordered, ordered[1:]):
            if tuple(later.ordered_messages[:len(prior.ordered_messages)]) != prior.ordered_messages:
                issues.append({"observation_id": later.observation_id,
                               "reason": "ordered_history_prefix_mismatch"})
            if prior.status.value != "completed":
                issues.append({"observation_id": later.observation_id,
                               "reason": "continuation_after_noncompleted_turn"})
    by_run_case: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for item in observations:
        lane = (item.sequence_id or "standalone")
        by_run_case[(item.run_id, item.evaluation_case_id)][lane].add(item.conversation_id)
    for lanes in by_run_case.values():
        ids = [conversation_id for lane_ids in lanes.values() for conversation_id in lane_ids]
        if len(ids) != len(set(ids)):
            issues.append({"observation_id": "run_case", "reason": "conversation_identifier_shared_across_lanes"})
    return {
        "status": "request_history_inconsistent" if issues else "request_history_consistent",
        "observation_count": len(observations), "conversation_count": len(groups),
        "condition_counts": dict(Counter(item.condition.value for item in observations)),
        "issues": issues,
        "provider_session_isolation": "unverifiable_from_request_history",
        "context_retention_proof": False,
        "note": "Distinct client conversation IDs and complete sent histories do not prove provider cache independence or model attention.",
    }
