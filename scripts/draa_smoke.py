"""CPU-only deterministic smoke check for uncalibrated DRAA Mode A/B."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.detection.models import DetectorResult, LayerOneReport, Severity
from core.draa import EvidenceExtractor


def main() -> dict[str, object]:
    report = LayerOneReport((DetectorResult("synthetic", 0.2, signal_scores={"injection": 0.2}),), 0.2, 0.0, 0.0, 0.2, Severity.NONE, None)
    record = EvidenceExtractor().build(identities={"evaluation_id": "smoke", "model_id": "mock"}, layer_one=report)
    return {"service": "securellmbench", "metric": "draa", "mode": "evidence", "status": record.status.value, "risk_score": record.risk_score}


if __name__ == "__main__":
    print(main())
