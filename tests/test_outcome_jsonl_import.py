import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from core.evaluation.attack_outcome import import_human_outcomes


def synthetic_import(text, suffix):
    path = Mock(spec=Path)
    path.suffix = suffix
    path.read_text.return_value = text
    return import_human_outcomes(path, evaluator_id="synthetic", evaluator_version="v1",
                                 label_version="v1", threat_model="synthetic")


def synthetic_record(identifier="a", success=True):
    return {"evaluation_id": identifier, "attack_family": "synthetic", "status": "classified", "success": success}


def test_multiline_jsonl_imports_every_synthetic_record():
    records = (synthetic_record("a", True), synthetic_record("b", False))
    text = "\n" + "\n\n".join(json.dumps(record) for record in records) + "\n"
    outcomes = synthetic_import(text, ".jsonl")

    assert len(outcomes) == 2
    assert [outcome.evaluation_id for outcome in outcomes] == ["a", "b"]
    assert [outcome.success for outcome in outcomes] == [True, False]


def test_single_jsonl_record_imports():
    outcomes = synthetic_import(json.dumps(synthetic_record()), ".jsonl")
    assert len(outcomes) == 1
    assert outcomes[0].success is True


def test_malformed_jsonl_line_raises_without_returning_labels():
    text = json.dumps(synthetic_record()) + "\n{malformed}\n"
    with pytest.raises(json.JSONDecodeError):
        synthetic_import(text, ".jsonl")


def test_missing_classified_success_is_not_inferred_as_safe():
    record = synthetic_record()
    del record["success"]
    with pytest.raises(ValueError, match="explicit boolean success"):
        synthetic_import(json.dumps(record), ".jsonl")


@pytest.mark.parametrize("wrapper", [False, True])
def test_existing_json_array_and_object_wrapper_still_import(wrapper):
    records = [synthetic_record()]
    text = json.dumps({"records": records} if wrapper else records)
    outcomes = synthetic_import(text, ".json")

    assert len(outcomes) == 1
    assert outcomes[0].success is True
