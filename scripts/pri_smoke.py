"""CPU-only deterministic smoke check for uncalibrated PRI Mode A/B."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pri.models import BenchmarkPopulationIdentity, PRIProfileCell, PRIStatus, SystemConfigurationIdentity
from core.pri.profile import PRIProfileBuilder


def main() -> dict[str, object]:
    profile = PRIProfileBuilder().build(
        SystemConfigurationIdentity("mock", "mock", "v1"),
        BenchmarkPopulationIdentity("synthetic", "v1", "synthetic-hash", "synthetic", "v1", "tax-v1", "synthetic", ("injection", "leakage")),
        cells=(PRIProfileCell("injection", None, "layer1", "synthetic", 0.2, "scalar", "detector-native", "detector-native", PRIStatus.APPLICABLE),),
    )
    return {"service": "securellmbench", "metric": "pri", "mode": "profile", "status": profile.status.value, "scalar_pri": profile.scalar_pri, "categories_requested": len(profile.population.requested_categories), "categories_observed": len(profile.population.observed_categories)}


if __name__ == "__main__":
    print(main())
