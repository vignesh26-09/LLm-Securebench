"""Network-free verification of the same controlled pipeline used by full runs."""
import json
import pytest
from dataclasses import replace
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import create_app
from core.dataset.benchmark_catalog import LARGE_KEY, load_selection
from core.inference.mock import MockInferenceProvider
from core.inference.contracts import ContextValidity, GenerationConfig
from core.models.registry import ModelMetadata
from core.judging.mock import MockJudgeProvider
from core.judging.models import JudgeConfig, JudgeDimension
from core.judging.prompting import JudgeRubric
from core.judging.service import JudgeService
from scripts.run_full_benchmark import run_full_model
from scripts.controlled_case_metrics import collect_case

INVENTORY = [{"name": "test-model", "digest": "fixture-digest"}]


def fixture_judge(n):
    outputs = [json.dumps({"dimension": dimension.value, "score": .8 if index % 2 else .4,
        "label": "ambiguous", "confidence": .5, "explanation": "Fixture only", "evidence_citations": []})
        for index in range(n * 10) for dimension in (JudgeDimension.SAFETY_STANCE, JudgeDimension.INSTRUCTION_FOLLOWING)]
    provider = MockJudgeProvider(outputs)
    config = JudgeConfig("mock-judge", "test-model", "fixture", "test", "test", "test")
    return JudgeService(provider, config, {dim: JudgeRubric(dim, "Fixture only")
        for dim in (JudgeDimension.SAFETY_STANCE, JudgeDimension.INSTRUCTION_FOLLOWING)})


def test_full_pipeline_persists_paired_and_sequential_metrics_and_resumes(tmp_path):
    url = f"sqlite:///{tmp_path / 'run.db'}"
    app = create_app(url)
    selection = load_selection(LARGE_KEY, count=2)
    provider = MockInferenceProvider()
    progress = []
    arguments = dict(database_url=url, run_id="fullfixture", provider=provider,
        judge=fixture_judge(2), inventory=INVENTORY, output_directory=tmp_path / "observations",
        progress_callback=lambda stage, **details: progress.append((stage, details)))
    # Only the unit-test fixture replaces the corpus size; the public API has no subset mode.
    with patch("scripts.run_full_benchmark.CORPUS_CASES", 2), patch("scripts.run_full_benchmark.load_selection", return_value=selection):
        outcome = run_full_model("test-model", **arguments)
        assert outcome["completed"] == 2
        assert len(provider.conversation_requests) == 20
        with pytest.raises(ValueError, match="Resume configuration"):
            run_full_model("test-model", **{**arguments, "context_window": 8192})
        resumed = run_full_model("test-model", **arguments)
        assert resumed == outcome
        assert len(provider.conversation_requests) == 20
    client = TestClient(app)
    report = client.get("/benchmark-runs/fullfixture/report").json()
    profiles = {item["family"]: item for item in report["metric_profiles"]}
    assert {"bsda", "rc", "saea", "draa", "pri", "dqi", "ml", "statistics"} <= set(profiles)
    assert profiles["bsda"]["record_count"] == 4
    assert profiles["saea"]["record_count"] == 2
    assert profiles["saea"]["status"] == "applicable"
    assert all(item["sample_count"] == 2 for item in profiles["saea"]["measurements"])
    assert profiles["saea"]["measured_case_count"] == 2
    assert profiles["rc"]["record_count"] == 2
    assert profiles["rc"]["status"] == "uncalibrated"
    assert profiles["ml"]["status"] == "blocked"
    assert report["selection"]["status"] == "evidence_review_required"
    assert all(item["latency_ms"] is not None for item in report["cases"])
    assert progress[-1][1]["completed_cases"] == 2
    # A fresh API instance can recover persisted job details after a restart.
    restarted = create_app(url)
    saved_job = TestClient(restarted).get('/benchmark-jobs/fullfixture').json()
    assert saved_job['status'] == 'completed'
    assert saved_job['completed_cases'] == 2
    restarted.state.session_factory.kw['bind'].dispose()
    app.state.session_factory.kw["bind"].dispose()


def test_api_refuses_subsets_and_requires_explicit_full_budget_confirmation():
    client = TestClient(create_app("sqlite:///:memory:", enable_local_runs=True), client=("127.0.0.1", 50010))
    headers = {"X-SecureLLM-Local": "1"}
    with patch("apps.api.local_execution.installed_models", return_value=INVENTORY), patch("apps.api.local_execution.threading.Thread") as thread:
        subset = client.post("/internal/benchmark-jobs", json={"model": "test-model", "case_count": 10}, headers=headers)
        assert subset.status_code == 422
        assert "10,000" in subset.json()["detail"]
        unconfirmed = client.post("/internal/benchmark-jobs", json={"model": "test-model"}, headers=headers)
        assert unconfirmed.status_code == 422
        assert "Confirm" in unconfirmed.json()["detail"]
        full = client.post("/internal/benchmark-jobs", json={"model": "test-model", "confirm_full_corpus": True}, headers=headers)
        assert full.status_code == 202
        assert full.json()["case_count"] == full.json()["total_cases"] == 10000
        assert full.json()["planned_target_calls"] == 100000
        assert thread.call_args.kwargs["args"][1]["full_corpus"] is True
        stopped = client.post(f"/internal/benchmark-jobs/{full.json()['id']}/stop", headers=headers)
        assert stopped.status_code == 200
        assert stopped.json()["status"] == "stopping"
        assert "current model call" in stopped.json()["stage"]
        again = client.post(f"/internal/benchmark-jobs/{full.json()['id']}/stop", headers=headers)
        assert again.status_code == 200
        assert again.json()["status"] == "stopping"
        assert client.post("/internal/benchmark-jobs", json={"model": "test-model", "confirm_full_corpus": True}, headers=headers).status_code == 409


def test_full_corpus_is_default_and_checksum_verified():
    selection = load_selection(LARGE_KEY)
    assert selection.count == len(selection.dataset.records) == 10000
    assert len({record.id for record in selection.dataset.records}) == 10000


def test_stop_preserves_partial_observations_and_resume_reuses_them(tmp_path):
    url = f"sqlite:///{tmp_path / 'stopped.db'}"
    selection = load_selection(LARGE_KEY, count=1)
    provider = MockInferenceProvider()
    arguments = dict(database_url=url, run_id="stoppedfixture", provider=provider,
        judge=fixture_judge(1), inventory=INVENTORY, output_directory=tmp_path / "observations")
    with patch("scripts.run_full_benchmark.CORPUS_CASES", 1), patch("scripts.run_full_benchmark.load_selection", return_value=selection):
        stopped = run_full_model("test-model", **arguments,
            stop_requested=lambda: len(provider.conversation_requests) >= 1)
        assert stopped["status"] == "stopped"
        assert stopped["completed"] == 0
        assert len(provider.conversation_requests) == 1
        app = create_app(url)
        saved = TestClient(app).get("/benchmark-jobs/stoppedfixture").json()
        assert saved["status"] == "stopped"
        assert saved["completed_cases"] == 0
        app.state.session_factory.kw["bind"].dispose()
        resumed = run_full_model("test-model", **arguments)
        assert resumed["status"] == "completed"
        assert resumed["completed"] == 1
        assert len(provider.conversation_requests) == 10  # The first observation was reused.


def test_guest_can_stop_only_a_local_showcase_run():
    app = create_app("sqlite:///:memory:", enable_local_runs=True, require_auth=True)
    client = TestClient(app, client=("127.0.0.1", 50012))
    headers = {"X-SecureLLM-Local": "1"}
    inventory = [{"name": "gemma3:4b", "digest": "fixture-digest"}]
    with patch("apps.api.local_execution.installed_models", return_value=inventory), patch("apps.api.local_execution.threading.Thread"):
        started = client.post("/internal/benchmark-jobs", json={"model": "gemma3:4b", "dataset_key": LARGE_KEY,
            "case_count": 10000, "confirm_full_corpus": True}, headers=headers)
        assert started.status_code == 202
        stopped = client.post(f"/internal/benchmark-jobs/{started.json()['id']}/stop", headers=headers)
        assert stopped.status_code == 200
        assert stopped.json()["status"] == "stopping"
        assert client.post(f"/internal/benchmark-jobs/{started.json()['id']}/stop").status_code == 403
    app.state.session_factory.kw["bind"].dispose()


def test_unknown_context_does_not_become_an_available_saea_score(tmp_path):
    class UnknownContextProvider(MockInferenceProvider):
        def generate_conversation(self, request):
            return replace(super().generate_conversation(request), context_status=ContextValidity.UNKNOWN)
    selection = load_selection(LARGE_KEY, count=1)
    result = collect_case(record=selection.dataset.records[0], evaluation_id="unknown-context",
        model=ModelMetadata("test-model", "mock"), generation=GenerationConfig(),
        run_id="unknowncontext", selection=selection, provider=UnknownContextProvider(),
        judge=fixture_judge(1), root=tmp_path)
    assert result["saea"].reason == "context_window_validity_not_established"
    assert result["saea"].trajectory.cumulative_vulnerability is None
    assert result["rc"].rc_auc_raw is None
    assert len(result["bsda"]) == 2
