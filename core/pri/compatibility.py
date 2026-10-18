"""Descriptive metadata compatibility checks; no ranking or tolerance policy."""

from dataclasses import dataclass

from core.pri.models import PRIProfileRecord


@dataclass(frozen=True, slots=True)
class PRICompatibilityResult:
    status: str
    reasons: tuple[str, ...]


def compare(left: PRIProfileRecord, right: PRIProfileRecord) -> PRICompatibilityResult:
    pairs = (
        ("benchmark_version", left.population.benchmark_version, right.population.benchmark_version),
        ("benchmark_hash", left.population.benchmark_hash, right.population.benchmark_hash),
        ("taxonomy_version", left.population.taxonomy_version, right.population.taxonomy_version),
        ("threat_model", left.population.threat_model, right.population.threat_model),
        ("policy_id", left.configuration.policy_id, right.configuration.policy_id),
        ("system_context_id", left.configuration.system_context_id, right.configuration.system_context_id),
        ("harness_id", left.configuration.harness_id, right.configuration.harness_id),
    )
    mismatches = tuple(name for name, a, b in pairs if a is not None and b is not None and a != b)
    if mismatches:
        return PRICompatibilityResult("incompatible", mismatches)
    unknown = tuple(name for name, a, b in pairs if a is None or b is None)
    return PRICompatibilityResult("unknown" if unknown else "compatible", unknown)
