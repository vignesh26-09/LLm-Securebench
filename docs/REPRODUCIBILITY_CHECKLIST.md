# Reproducibility checklist

- [ ] Freeze and checksum an approved research dataset; record version, license/access basis, and sampling/exclusions. The controlled CLI currently records a declared hash without independently verifying source bytes.
- [ ] Lock the RQs, outcome rubric, analysis plan, model set, related-prompt groups, and amendments before production runs. Record preregistration IDs.
- [ ] Record exact target and evaluator model IDs/digests, runtime/provider versions, quantization where available, context window, temperature, top-p, output limit, seeds, and effective seed support.
- [ ] Preserve immutable baseline, isolated, sequential, benign-control, and recovery observations, including failures and ordered messages. The benign-control condition is not yet implemented by the current runner.
- [ ] Store manifest and artifact hashes, code revision, dependency versions, hardware/runtime metadata, and start/end times.
- [ ] Assess context/canary evidence probabilistically and inspect contamination ledger; block suspect SAEA controls.
- [ ] Export source-hashed blinded annotation candidates, obtain two independent human judgments, adjudicate conflicts, and keep the join map private.
- [ ] Freeze evaluator split groups and check leakage before tuning; report coverage, confusion counts, uncertainty, and held-out performance.
- [ ] Report every metric's applicable count, excluded counts, versions, label source, and missingness. Do not plot fixture or engineering records as Phase 1 results.
- [ ] Replay from archived artifacts, report factual differences, and retain original and amended records independently.

Verification command: set `TEMP` and `TMP` to `F:\SecureLLM.tmp`, then run `F:\SecureLLM\.venv\Scripts\python.exe -m pytest -q` from the project root. Real model execution additionally requires already-installed Ollama models and the local service; no model is downloaded by the project.
