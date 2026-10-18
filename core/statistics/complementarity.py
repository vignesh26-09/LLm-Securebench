"""Raw paired complementarity tables with explicitly exploratory thresholds."""

from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ComplementarityRow:
    pair_id: str
    asr_left: float | None
    asr_right: float | None
    trajectory_left: float | None
    trajectory_right: float | None
    groups: Mapping[str, str] = field(default_factory=dict)


def complementarity_table(rows: Sequence[ComplementarityRow], *,
                          similar_outcome_threshold: float | None = None,
                          material_trajectory_threshold: float | None = None) -> dict[str, object]:
    exploratory = similar_outcome_threshold is not None or material_trajectory_threshold is not None
    flagged = []
    if similar_outcome_threshold is not None and material_trajectory_threshold is not None:
        for row in rows:
            if None in (row.asr_left, row.asr_right, row.trajectory_left, row.trajectory_right):
                continue
            if abs(row.asr_left - row.asr_right) <= similar_outcome_threshold and abs(row.trajectory_left - row.trajectory_right) >= material_trajectory_threshold:
                flagged.append(row.pair_id)
    return {"rows": tuple(rows), "status": "exploratory" if exploratory else "raw_only",
            "thresholds": {"similar_outcome": similar_outcome_threshold,
                           "material_trajectory": material_trajectory_threshold},
            "flagged_pair_ids": tuple(flagged),
            "scientifically_validated": False,
            "reason": "thresholds_are_user_configured_exploratory_values" if exploratory else None}
