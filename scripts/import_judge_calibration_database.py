"""Import the verified, repository-held JailbreakBench calibration artifact once."""

from pathlib import Path

from sqlalchemy.orm import Session

from core.persistence.database import make_engine
from core.reporting.imports import import_persisted_judge_calibration


ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    engine = make_engine(f"sqlite:///{ROOT / 'securellmbench.db'}")
    with Session(engine) as session:
        print({"imported": import_persisted_judge_calibration(
            session, ROOT / "experiments" / "jailbreakbench-validation" / "calibration_artifact_v1.json")})
