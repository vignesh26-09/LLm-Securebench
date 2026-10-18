"""CPU-only deterministic smoke check for the provider-neutral SAEA core."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.saea import SAEAEngine, SAEAInput
from core.saea.models import AttackInstance, BehavioralState, ContextStatus, SpacingCondition


def main() -> dict[str, object]:
    baseline = BehavioralState("baseline", {"safety": 0.0, "helpfulness": 0.0})
    isolated = BehavioralState("isolated", {"safety": 0.2, "helpfulness": 0.2})
    attack_state = BehavioralState("attack", {"safety": 0.4, "helpfulness": 0.4})
    attack = AttackInstance("safe-1", "safe", "synthetic", "smoke", 1, "case", attack_state, isolated, (baseline,))
    result = SAEAEngine().evaluate(SAEAInput("smoke", "saea-smoke", "mock", "synthetic", "v1", (baseline,), (attack,), SpacingCondition.STACKED, ContextStatus.RETAINED))
    return {"service": "securellmbench", "metric": "saea", "status": result.status.value, "synergy_status": result.synergy.status.value}


if __name__ == "__main__":
    print(main())
