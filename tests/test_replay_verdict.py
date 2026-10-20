import pytest

from core.experiments.replication import compare_replay, export_bundle


def replay_fixture():
    observations = ({"observation_id": "synthetic", "response": "synthetic", "context_status": "retained"},)
    signals = {"synthetic": {"status": "completed", "value": 0.25}}
    bundle = export_bundle(bundle_id="synthetic", specification={}, observations=observations,
                           layer1_signals=signals, layer2_signals=signals)
    return bundle, observations, signals


@pytest.mark.parametrize("layer", ["layer1", "layer2"])
def test_signal_difference_prevents_identical_overall_verdict(layer):
    bundle, observations, signals = replay_fixture()
    layers = {"replay_layer1_signals": signals, "replay_layer2_signals": signals}
    layers[f"replay_{layer}_signals"] = {"synthetic": {"status": "completed", "value": 0.75}}
    report = compare_replay(bundle, observations, replay_id="synthetic", **layers)

    assert getattr(report.differences[0], f"{layer}_status") == "different"
    assert report.status == "differences_observed"


@pytest.mark.parametrize("layer", ["layer1", "layer2"])
def test_missing_exported_signal_prevents_identical_overall_verdict(layer):
    bundle, observations, signals = replay_fixture()
    layers = {"replay_layer1_signals": signals, "replay_layer2_signals": signals}
    layers[f"replay_{layer}_signals"] = {}
    report = compare_replay(bundle, observations, replay_id="synthetic", **layers)

    assert getattr(report.differences[0], f"{layer}_status") == "replay_signal_unavailable"
    assert report.status == "differences_observed"


@pytest.mark.parametrize("export_signals", [False, True])
def test_no_differences_preserve_identical_verdict(export_signals):
    bundle, observations, signals = replay_fixture()
    if not export_signals:
        bundle = export_bundle(bundle_id="synthetic", specification={}, observations=observations)
    report = compare_replay(bundle, observations, replay_id="synthetic",
                            replay_layer1_signals=signals if export_signals else None,
                            replay_layer2_signals=signals if export_signals else None)

    assert report.status == "identical"
