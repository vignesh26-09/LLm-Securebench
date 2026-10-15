# Python environment repair and reproduction

**Status:** repaired in place on 2026-10-11. `F:\SecureLLM\.venv\Scripts\python.exe` now launches Python **3.12.14**. The prior virtual environment was created with Python **3.12.10** at `C:\Users\tirishaanth\AppData\Local\Programs\Python\Python312\python.exe`; `.venv\pyvenv.cfg` still pointed there after that installation disappeared. The Windows venv launcher therefore could not start. `py -3.12` also resolved to a missing system path and was not used for the repair.

The functioning base interpreter is `C:\Users\tirishaanth\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` (3.12.14). A throwaway venv created from it launched successfully. Before repair, `.venv\pyvenv.cfg`, the old launchers, and a 43-distribution version snapshot were saved under `F:\SecureLLM\.tmp\phase6-venv-backup\`. The bundled interpreter then ran `-m venv --upgrade F:\SecureLLM\.venv`, which replaced the venv launchers/configuration **without replacing its site-packages**. The throwaway probe was removed; the backup remains available for rollback. No unrelated files or repository data were moved.

The before/after distribution snapshots were identical (43 installed distributions, SHA-256 `99518e5e377e7fe59c1605dfd8b4c3f7d099fb829ebb98dd150084006decafab`). A copy is [PYTHON_ENVIRONMENT_SNAPSHOT.txt](/F:/SecureLLM/docs/PYTHON_ENVIRONMENT_SNAPSHOT.txt). This records the exact observed versions; `pyproject.toml` retains its original version ranges and there was no separate Python lockfile. Key verified versions are SecureLLMBench 0.1.0, pytest 8.4.2, FastAPI 0.141.1, SQLAlchemy 2.1.1, Pydantic 2.13.5, HTTPX 0.28.1, and Matplotlib 3.11.2. `python -m pip check` reports no broken requirements. The venv's `pip.exe`, `pytest.exe`, and `uvicorn.exe` launchers were also verified; the reproducibility commands below use `python -m` where possible.

`F:\SecureLLM.tmp` is the designated temporary directory. An explicit Python temporary file and `tempfile.gettempdir()` resolved there when the command had write access. A workspace-restricted sandbox can force Python to fall back to the Windows temp directory despite `TEMP`/`TMP`; use the same approved directory access for exact reproduction.

Run from `F:\SecureLLM` in PowerShell:

```powershell
$env:TEMP='F:\SecureLLM.tmp'; $env:TMP='F:\SecureLLM.tmp'
& .\.venv\Scripts\python.exe --version
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe scripts/api_smoke.py
& .\.venv\Scripts\python.exe scripts/prepare_phase5_annotation.py
```

Observed after repair: **215 passed, 1 Starlette/HTTPX deprecation warning**; API smoke returned health/ready 200, review creation 201, eight successful read-resource checks, and `scientific_claims_validated=False`. The annotation package re-audit returned 36 blank samples and the unchanged manifest SHA-256 `a01febdf5f9d5fe5459490e593545cdfa3206580ed8aca2723cb456747c25245`.

The venv's base interpreter is a Codex-bundled runtime. If that cache is later removed, point a new venv at another installed Python 3.12, preserve the recorded dependency versions, and rerun the commands above. Do not assume the Windows `py` launcher currently identifies a usable base installation.
