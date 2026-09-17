import json
import subprocess
import sys
import unittest
from pathlib import Path

from core.inference.mock import MockInferenceProvider
from core.judging.mock import MockJudgeProvider

from experiments.paper_2026.run_experiment import _judge_service, _prompts, _run, _stage_context


ROOT = Path(__file__).resolve().parents[1]


class PaperExperimentDryRunTests(unittest.TestCase):
    def test_fixture_dry_run_exports_complete_trace_and_analysis(self):
        output = ROOT / ".tmp" / "paper-fixture-trace.json"
        analysis = ROOT / ".tmp" / "paper-fixture-analysis.json"
        subprocess.run([sys.executable, str(ROOT / "experiments/paper_2026/run_experiment.py"), "--fixture-dry-run", "--output", str(output)], check=True, cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / "experiments/paper_2026/analyze_results.py"), "--input", str(output), "--output", str(analysis)], check=True, cwd=ROOT)
        trace = json.loads(output.read_text(encoding="utf-8"))
        result = json.loads(analysis.read_text(encoding="utf-8"))
        for key in ("responses", "layer1", "layer2", "bsda", "rc", "saea", "draa", "pri", "statistics", "asr"):
            self.assertIn(key, trace)
        self.assertFalse(trace["scientifically_validated"])
        self.assertFalse(trace["paper_usable"])
        self.assertEqual(trace["generation"]["max_new_tokens"], 512)
        self.assertIsNone(trace["bsda"]["composite"])
        self.assertIsNone(trace["draa"]["risk_score"])
        self.assertIsNone(trace["pri"]["scalar_pri"])
        self.assertEqual(trace["rc"]["status"], "undefined")
        self.assertEqual(trace["rc"]["reason"], "context_window_validity_not_established")
        self.assertEqual(trace["saea"]["status"], "undefined")
        self.assertIsNone(trace["asr"]["attack_success_rate"])
        self.assertFalse(result["scientifically_validated"])
        self.assertIn("asr", result["blocked"])

    def test_unavailable_judge_dimensions_do_not_become_metric_scores(self):
        prompts = _prompts()
        responses = {
            prompts["baseline"]: "Safe policy summary.",
            prompts["isolated_attack"]: "I cannot reveal secrets.",
            prompts["sequential"][0]: "I cannot reveal secrets.",
            prompts["sequential"][1]: "I will not bypass safety.",
            prompts["recovery"][0]: "Safe policy summary.",
        }
        target = MockInferenceProvider(responses)
        judge = _judge_service(MockJudgeProvider(("not json",) * 10), "mock-judge", "mock-judge-model", "fixture")

        trace = _run("fixture-target", "mock", "fixture-model-v1", target, judge, "paper-2026-unavailable-fixture-v1", fixture=True)

        self.assertEqual(trace["rc"]["status"], "failed_evaluation")
        self.assertIsNone(trace["rc"]["rc_auc_raw"])
        self.assertEqual(trace["saea"]["status"], "undefined")
        self.assertIsNone(trace["saea"]["trajectory"]["cumulative_vulnerability"])
        self.assertTrue(any(item["score"] is None for item in trace["layer2"]["baseline"]))

    def test_stage_context_uses_the_stage_prompt_and_legitimate_success_criterion(self):
        prompts = _prompts()
        baseline = _stage_context("baseline", prompts)
        attack = _stage_context("isolated_attack", prompts)
        recovery = _stage_context("recovery_1", prompts)
        self.assertEqual(baseline[0], prompts["baseline"])
        self.assertIn("safety policy summary", baseline[1])
        self.assertEqual(attack[0], prompts["isolated_attack"])
        self.assertIn("Refuse secret extraction", attack[1])
        self.assertEqual(recovery[0], prompts["recovery"][0])


if __name__ == "__main__":
    unittest.main()
