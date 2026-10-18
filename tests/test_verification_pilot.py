import json
from scripts.run_verification_pilot import atomic_json, check_gate

def test_gate_requires_all_three_complete_models():
    rows=[{'completed':10,'failed':0} for _ in range(3)]
    assert check_gate(rows)
    assert not check_gate(rows[:2])
    rows[-1]={'completed':9,'failed':1}
    assert not check_gate(rows)

def test_checkpoint_atomic_update(tmp_path):
    path=tmp_path/'state.json'
    atomic_json(path,{'completed':1})
    atomic_json(path,{'completed':2})
    assert json.loads(path.read_text())=={'completed':2}
    assert not path.with_suffix('.pending').exists()


def test_checkpoint_retries_transient_windows_access_error(tmp_path, monkeypatch):
    from pathlib import Path
    from scripts import run_verification_pilot as runner
    original=Path.replace
    attempts=[]
    def replace(source,target):
        attempts.append(source)
        if len(attempts)==1:
            raise PermissionError('synthetic Windows sharing violation')
        return original(source,target)
    monkeypatch.setattr(Path,'replace',replace)
    monkeypatch.setattr(runner.time,'sleep',lambda seconds: None)
    path=tmp_path/'state.json'
    atomic_json(path,{'completed':29})
    assert json.loads(path.read_text())=={'completed':29}
    assert len(attempts)==2


def test_checkpoint_permanent_failure_preserves_previous_state(tmp_path, monkeypatch):
    import pytest
    from pathlib import Path
    from scripts import run_verification_pilot as runner
    path=tmp_path/'state.json'
    atomic_json(path,{'completed':29})
    attempts=[]
    def blocked(source,target):
        attempts.append(source)
        raise PermissionError('synthetic persistent access failure')
    monkeypatch.setattr(Path,'replace',blocked)
    monkeypatch.setattr(runner.time,'sleep',lambda seconds: None)
    with pytest.raises(PermissionError):
        atomic_json(path,{'completed':30})
    assert len(attempts)==6
    assert json.loads(path.read_text())=={'completed':29}
