"""Export real completed controlled observations for blinded human review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.evaluation.annotation_candidates import candidates_from_observations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--objectives", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    objectives = json.loads(args.objectives.read_text(encoding="utf-8"))
    value = candidates_from_observations(args.observations, objectives,
                                         experiment_id=args.experiment_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"candidates": len(value["candidates"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
