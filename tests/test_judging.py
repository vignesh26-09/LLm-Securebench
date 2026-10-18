"""Safe synthetic tests for provider-neutral Layer 2 semantic-judge architecture."""

import json
import tempfile
import unittest
from pathlib import Path

from core.judging.models import JudgeCase, JudgeConfig, JudgeDimension, JudgeLabel, JudgmentStatus
from core.judging.mock import MockJudgeProvider, timeout_error
from core.judging.prompting import JudgeExemplar, JudgeRubric
from core.judging.service import JudgeService
from core.judging.storage import JsonJudgeResultStore


def valid_output(dimension: JudgeDimension, *, score: float = 0.8) -> str:
    return json.dumps({
        "dimension": dimension.value,
        "score": score,
        "label": "pass",
        "confidence": 0.7,
        "explanation": "Safe synthetic evaluation evidence.",
        "evidence_citations": ["synthetic evidence"],
        "metadata": {"grounding_sufficiency": "adequate"},
    })


class JudgeServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = JudgeConfig(
            provider_name="mock-judge", model="mock-judge-model", model_version="test-v1",
            methodology_version="layer2-spec-0.1", prompt_version="prompt-v1", rubric_version="rubric-v1",
            temperature=0.0, seed=123, timeout_seconds=1.0,
        )
        self.case = JudgeCase(
            evaluation_id="evaluation-safe-1", case_id="case-safe-1",
            prompt="Provide a concise factual summary using the supplied reference.",
            response="The supplied reference says the test item is blue.",
            reference_material="The test item is blue.", success_criteria="Use only the supplied reference.",
        )
        exemplar = JudgeExemplar("Synthetic prompt", "Synthetic response", "pass", 0.8, "Synthetic rationale")
        self.rubrics = {
            dimension: JudgeRubric(dimension, f"Synthetic rubric for {dimension.value}.", ("Do not infer beyond supplied material.",), (exemplar,), "rubric-v1")
            for dimension in JudgeDimension
        }

    def _service(self, outputs: list[str | Exception], *, retries: int = 0) -> tuple[JudgeService, MockJudgeProvider]:
        provider = MockJudgeProvider(outputs)
        config = JudgeConfig(**{**self.config.__dict__} if hasattr(self.config, "__dict__") else {
            "provider_name": self.config.provider_name, "model": self.config.model, "model_version": self.config.model_version,
            "methodology_version": self.config.methodology_version, "prompt_version": self.config.prompt_version, "rubric_version": self.config.rubric_version,
            "temperature": self.config.temperature, "seed": self.config.seed, "timeout_seconds": self.config.timeout_seconds, "max_retries": retries,
        })
        return JudgeService(provider, config, self.rubrics), provider

    def test_completed_result_preserves_structured_measurement_metadata(self) -> None:
        service, provider = self._service([valid_output(JudgeDimension.CORRECTNESS)])
        with self.assertLogs("core.judging.service", level="INFO") as logs:
            result = service.judge(self.case, JudgeDimension.CORRECTNESS, run_metadata={"run_id": "safe-run"})
        self.assertEqual(result.status, JudgmentStatus.COMPLETED)
        self.assertEqual(result.score, 0.8)
        self.assertEqual(result.label, JudgeLabel.PASS)
        self.assertEqual(result.evaluation_id, "evaluation-safe-1")
        self.assertEqual(result.judge_model, "mock-judge-model")
        self.assertEqual(result.prompt_version, "prompt-v1")
        self.assertTrue(result.generation_metadata["deterministic"])
        self.assertEqual(result.run_metadata["run_id"], "safe-run")
        self.assertIn("model=mock-judge-model", logs.output[0])
        self.assertNotIn("mock-judge-model", provider.requests[0].prompt)

    def test_missing_grounding_skips_correctness_without_zero_score(self) -> None:
        service, provider = self._service([])
        ungrounded = JudgeCase("eval-2", "case-2", "Open question", "Synthetic response")
        result = service.judge(ungrounded, JudgeDimension.CORRECTNESS)
        self.assertEqual(result.status, JudgmentStatus.SKIPPED)
        self.assertFalse(result.applicable)
        self.assertEqual(result.applicability_reason, "grounding_material_missing")
        self.assertIsNone(result.score)
        self.assertEqual(provider.requests, [])

    def test_dimension_specific_applicability_rules_skip_without_provider_calls(self) -> None:
        service, provider = self._service([])
        bare_case = JudgeCase("eval-3", "case-3", "Open task", "Synthetic response")
        for dimension in (JudgeDimension.HALLUCINATION, JudgeDimension.INSTRUCTION_FOLLOWING, JudgeDimension.SAFETY_STANCE, JudgeDimension.SEMANTIC_DRIFT, JudgeDimension.REASONING_QUALITY, JudgeDimension.CONSISTENCY):
            result = service.judge(bare_case, dimension)
            self.assertEqual(result.status, JudgmentStatus.SKIPPED)
            self.assertIsNone(result.score)
        self.assertEqual(provider.requests, [])

    def test_malformed_json_is_recovered_when_a_single_json_object_is_present(self) -> None:
        service, _ = self._service(["Preamble ignored. " + valid_output(JudgeDimension.CORRECTNESS)])
        result = service.judge(self.case, JudgeDimension.CORRECTNESS)
        self.assertEqual(result.status, JudgmentStatus.COMPLETED)
        self.assertTrue(result.generation_metadata["json_recovered"])

    def test_known_same_dimension_alias_is_normalized_with_provenance(self) -> None:
        output = json.loads(valid_output(JudgeDimension.SAFETY_STANCE))
        output["dimension"] = "safety"
        service, _ = self._service([json.dumps(output)])
        case = JudgeCase("eval-safety", "case-safety", self.case.prompt, self.case.response,
                         attack_type_definition="synthetic prompt injection")
        result = service.judge(case, JudgeDimension.SAFETY_STANCE)
        self.assertEqual(result.status, JudgmentStatus.COMPLETED)
        self.assertEqual(result.generation_metadata["judge_output_metadata"]["reported_dimension"], "safety")
        self.assertEqual(result.generation_metadata["judge_output_metadata"]["dimension_normalized"], "safety_stance")

    def test_malformed_output_retries_then_succeeds(self) -> None:
        service, provider = self._service(["not json", valid_output(JudgeDimension.CORRECTNESS)], retries=1)
        result = service.judge(self.case, JudgeDimension.CORRECTNESS)
        self.assertEqual(result.status, JudgmentStatus.COMPLETED)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(len(provider.requests), 2)

    def test_timeout_and_invalid_output_are_recorded_as_failures(self) -> None:
        timeout_service, _ = self._service([timeout_error()])
        timeout_result = timeout_service.judge(self.case, JudgeDimension.CORRECTNESS)
        self.assertEqual(timeout_result.status, JudgmentStatus.FAILED)
        self.assertEqual(timeout_result.failure["type"], "JudgeTimeoutError")
        invalid_service, _ = self._service([json.dumps({"dimension": "wrong", "label": "pass", "score": 0.8})])
        invalid_result = invalid_service.judge(self.case, JudgeDimension.CORRECTNESS)
        self.assertEqual(invalid_result.status, JudgmentStatus.FAILED)
        self.assertEqual(invalid_result.failure["type"], "JudgeOutputValidationError")

    def test_refusal_is_unscored_and_machine_readable(self) -> None:
        refusal = json.dumps({"dimension": "correctness", "score": None, "label": "refuse", "reason": "Synthetic reference ambiguity.", "metadata": {}})
        service, _ = self._service([refusal])
        result = service.judge(self.case, JudgeDimension.CORRECTNESS)
        self.assertEqual(result.status, JudgmentStatus.REFUSED)
        self.assertIsNone(result.score)
        self.assertEqual(result.uncertainty_reason, "Synthetic reference ambiguity.")
        with tempfile.TemporaryDirectory() as directory:
            store = JsonJudgeResultStore(Path(directory))
            store.save(result)
            self.assertEqual(store.load(result.evaluation_id, result.dimension), result)
