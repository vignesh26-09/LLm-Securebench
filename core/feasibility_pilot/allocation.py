"""Pre-response allocation; assignment identity never depends on observations."""

from dataclasses import dataclass
from enum import StrEnum

from core.feasibility_pilot.cases import digest
from core.feasibility_pilot.restricted_store import EvidenceConflict


class Arm(StrEnum):
    B0 = "B0"
    B1 = "B1"
    T = "T"
    R = "R"
    A = "A"
    I = "I"
    S = "S"


DISTANCES = {Arm.B0: frozenset({None}), **{
    arm: frozenset({0, 2, 5}) for arm in Arm if arm != Arm.B0}}
LIVE_ARMS = frozenset({Arm.B0, Arm.B1, Arm.T, Arm.R, Arm.A, Arm.I})


@dataclass(frozen=True, slots=True)
class TrialAssignment:
    protocol_sha256: str
    model_id: str
    goal_id: str
    repetition: int
    arm: Arm
    distance: int | None
    probe_variant_id: str
    probe_version: int
    seed: int
    script_version: str
    trial_id: str
    matching_set_id: str | None
    secret_reference: str
    evidence_class: str

    @property
    def live_primary_eligible_arm(self) -> bool:
        return self.arm in {Arm.A, Arm.T}


def allocate_trial(*, protocol_sha256: str, model_id: str, goal_id: str,
                   repetition: int, arm: Arm, distance: int | None,
                   probe_variant_id: str, probe_version: int, seed: int,
                   script_version: str) -> TrialAssignment:
    if distance not in DISTANCES[arm]:
        raise ValueError("Arm-distance cell is inapplicable")
    if (not protocol_sha256 or not model_id or not goal_id or not probe_variant_id
            or not script_version or repetition < 1 or probe_version < 1):
        raise ValueError("Incomplete frozen allocation")
    identity = (protocol_sha256, model_id, goal_id, repetition, arm.value,
                distance, probe_variant_id, probe_version, seed, script_version)
    trial_id = "trial." + digest(identity)[:32]
    matching_set_id = ("pair." + digest((protocol_sha256, model_id, goal_id,
                                         repetition, distance))[:32]
                       if arm in {Arm.A, Arm.T} else None)
    return TrialAssignment(protocol_sha256, model_id, goal_id, repetition, arm,
                           distance, probe_variant_id, probe_version, seed,
                           script_version, trial_id, matching_set_id,
                           f"secret.{trial_id}",
                           "scripted_mechanism" if arm == Arm.S else "live_feasibility_pilot")


def counterbalanced_variant(variants: tuple[str, str], repetition: int,
                            arm: Arm, *, seed: int) -> str:
    """Balance A/T variants over repetitions without examining responses."""
    if arm not in {Arm.A, Arm.T} or len(variants) != 2 or variants[0] == variants[1]:
        raise ValueError("Counterbalancing requires two distinct A/T variants")
    return variants[(seed + repetition + (arm == Arm.T)) % 2]


class AllocationLedger:
    def __init__(self) -> None:
        self._by_id: dict[str, TrialAssignment] = {}
        self._frozen = False

    def add(self, assignment: TrialAssignment) -> None:
        if self._frozen:
            raise EvidenceConflict("Allocation is frozen")
        if assignment.trial_id in self._by_id:
            raise EvidenceConflict("Duplicate trial identity")
        self._by_id[assignment.trial_id] = assignment

    def freeze(self) -> str:
        validate_at_pairs(self.assignments)
        self._frozen = True
        return self.sha256

    @property
    def sha256(self) -> str:
        from dataclasses import asdict
        return digest([asdict(self._by_id[key]) for key in sorted(self._by_id)])

    @property
    def assignments(self) -> tuple[TrialAssignment, ...]:
        return tuple(self._by_id.values())

    def get(self, trial_id: str) -> TrialAssignment:
        return self._by_id[trial_id]

    @property
    def frozen(self) -> bool:
        return self._frozen


def validate_at_pairs(assignments: tuple[TrialAssignment, ...]) -> None:
    by_pair: dict[str, dict[Arm, TrialAssignment]] = {}
    for item in assignments:
        if item.arm in {Arm.A, Arm.T}:
            assert item.matching_set_id is not None
            members = by_pair.setdefault(item.matching_set_id, {})
            if item.arm in members:
                raise ValueError("Duplicate A/T pair arm")
            members[item.arm] = item
    for members in by_pair.values():
        if set(members) != {Arm.A, Arm.T}:
            raise ValueError("Unpaired A/T assignment")
        if (members[Arm.A].probe_variant_id == members[Arm.T].probe_variant_id
                or members[Arm.A].probe_version != members[Arm.T].probe_version):
            raise ValueError("A/T probe variants are not complementary and version-matched")

