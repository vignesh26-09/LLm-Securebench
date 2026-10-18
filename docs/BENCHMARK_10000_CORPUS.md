# 10,000-prompt engineering corpus

The ordinary benchmark workspace now offers 10,000 **distinct source prompts**. It does not contain 10,000 completed model evaluations. This collection is an engineering workload, separate from the controlled feasibility pilot and its seven-arm protocol. Importing the corpus did not run a model, create human labels, or change any BSDA, RC, or SAEA formula.

## Sources and derivation

| Group | Count | Pinned source | Local source SHA-256 | Extraction |
|---|---:|---|---|---|
| Benign task sources | 5,000 | [Databricks Dolly 15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k), revision `bdd27f4d94b9c1f951818a7da7fd7aeea5dbff1a`, CC BY-SA 3.0 | `2df9083338b4abd6bceb5635764dab5d833b393b55759dffb0959b6fcbf794ec` | Employee-written instruction with empty context. The published response is not imported as a new model observation. |
| Historical red-team seeds | 5,000 | [Anthropic HH-RLHF red-team attempts](https://huggingface.co/datasets/Anthropic/hh-rlhf), revision `09be8c5bbc57cb3887f3a9732ad6aa7ec602a1fa`, MIT repository metadata | `4c7b0069991460f0064f279fd400b51f3f0095697d14d7793c49b0925f80814f` | First user turn only. Historical assistant turns, ratings, and subsequent turns are not presented as fresh defender responses or outcome labels. |

The builder checks both source hashes, selects by a deterministic SHA-256 rank of source row IDs, filters obvious email and telephone formats and prompts outside 10–4,000 characters, and removes normalized exact duplicates. It interleaves the two groups. The frozen processed JSONL has 10,000 rows, 10,000 distinct normalized prompts, and SHA-256 `c718be89edc465663f5ae367539b5979d51e6ad467bd76097648acef9b8083da`. The tracked [manifest](../data/benchmark_10000.manifest.json) records source revisions, checksums, categories, and limitations. Raw and processed prompt files remain local and Git-ignored.

“Benign” here describes the source task, **not** a topic-matched experimental control. A first turn extracted from a multi-turn red-team transcript may be incomplete as a standalone attack. Obvious-identifier filtering does not certify the absence of personal information; operators must review content and access controls before external distribution or remote-provider use. Neither group has independently verified attack-success labels. These records cannot support ASR, model-safety rankings, a controlled attack/benign effect estimate, or paper-ready novelty claims.

## Reproduce and use

Run from `F:\SecureLLM` with `TEMP` and `TMP` set to `F:\SecureLLM.tmp`:

```powershell
$env:TEMP = 'F:\SecureLLM.tmp'
$env:TMP = 'F:\SecureLLM.tmp'
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\build_10000_corpus.py --download
& 'F:\SecureLLM\.venv\Scripts\python.exe' scripts\import_repository_data.py --large
& 'F:\SecureLLM\.venv\Scripts\python.exe' -m pytest tests\test_large_benchmark_corpus.py -q
```

The builder downloads only the two pinned files, verifies their hashes, and refuses to overwrite a differing versioned output. The importer saves only a dataset manifest in SQLite; prompt text remains in the local ignored JSONL until a chosen batch is run. The API advertises availability and limits at `GET /benchmark-datasets`.

Choose **10,000 sourced prompts** on `/benchmark`, then set a 1-based start case and a count of 1–1,000. The default is 100. Ten consecutive 1,000-case jobs cover the corpus without altering the case assignments; jobs execute only after an explicit local submission with an installed model. A selected run records the source hash, case offset/count, model configuration, responses, failures, and detector observations. A failed or unrun case is not a non-leak. Runs on different windows are descriptive records and should not be interpreted as a matched model comparison. Long jobs have no per-case durable resume checkpoint; use smaller batches when interruption risk matters.
