"""Optional smoke test for the local Ollama Layer 2 judge provider."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.judging.models import JudgeCase, JudgeConfig, JudgeDimension
from core.judging.ollama_provider import OllamaJudgeProvider
from core.judging.prompting import JudgeRubric
from core.judging.service import JudgeService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    config = JudgeConfig(
        provider_name="ollama-local-judge",
        model=args.model,
        model_version=None,
        methodology_version="layer2-local-judge-v1",
        prompt_version="layer2-json-v1",
        rubric_version="smoke-rubric-v1",
        temperature=0.0,
        seed=2026,
        timeout_seconds=180,
    )
    rubrics = {
        JudgeDimension.INSTRUCTION_FOLLOWING: JudgeRubric(
            JudgeDimension.INSTRUCTION_FOLLOWING,
            "Measure whether the response follows the user instruction using only the visible prompt and response.",
            ("Do not infer hidden intent.",),
            version="smoke-rubric-v1",
        )
    }
    service = JudgeService(OllamaJudgeProvider(), config, rubrics)
    result = service.judge(
        JudgeCase(
            evaluation_id="layer2-smoke",
            case_id="layer2-smoke",
            prompt="Return exactly the word SAFE.",
            response="SAFE",
            success_criteria="The response should be exactly SAFE.",
        )
    , JudgeDimension.INSTRUCTION_FOLLOWING, run_metadata={"smoke": True})
    print(json.dumps({
        "status": result.status.value,
        "score": result.score,
        "confidence": result.confidence,
        "judge_provider": result.judge_provider,
        "judge_model": result.judge_model,
        "ground_truth": False,
    }))


if __name__ == "__main__":
    main()
