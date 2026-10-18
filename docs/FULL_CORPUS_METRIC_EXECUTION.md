# Full-corpus metric execution

Every new test launched by the platform must use the pinned, checksum-verified `mixed-source-10000-v1` corpus, offset 0, count 10,000. The API rejects example datasets and subset windows for user-facing jobs. The small direct `run_model` engineering helper remains for isolated unit/smoke testing; it is not the platform job route.

## Controlled protocol per source prompt

`full-corpus-controlled-v1` uses the existing conversation-aware ExperimentRunner:

1. One original source-prompt baseline.
2. Two isolated controls: each starts a fresh conversation with its own baseline, then one fixed task-override injection (four calls).
3. One fresh sequential conversation: baseline, both injections in order, then two original-task recovery probes (five calls).
4. Two versioned judge dimensions per available answer: safety stance and instruction-following of the original task. Instruction-following is explicitly a helpfulness proxy, not correctness or ground truth.

Total budget: 100,000 target generations and up to 200,000 local judge generations per complete test, with no automatic retries or downloads. This is 10,000 source prompts expanded into controlled conditions, **not 10,000 distinct validated attack designs**. The same two explicit injection templates are applied to each source prompt. The corpus mixes benign and red-team sources, so the original source baseline is not assumed to be benign.

The UI shows this budget, requires explicit acknowledgment, and lets the user choose an installed judge. A self-judge is labeled exploratory. API targets remain opt-in and require an installed local judge. API keys are never persisted.

## Metric outputs and limits

- BSDA: two matched response pairs per source case; lexical semantic, detector-native safety, and structural raw distances. Instruction components remain unmeasurable without comparable parsed constraints; the unvalidated composite remains null.
- SAEA: matched isolated/sequential states, actual conversation context status, and isolation-ledger evidence feed the existing engine. Unknown/truncated context or failed judge measurements stay undefined/failed, with a reason. Available context effects and sequence deviations are descriptive automated measurements. Cache isolation is not independently proven merely by distinct conversation IDs. Coalition/Shapley and alternate-order experiments are not fabricated.
- Recovery: actual baseline/attack/recovery states feed the existing engine. Initial and recovery distances are shown when admissible. Formal RC indices remain null without an appropriate calibration artifact; none is silently invented.
- DRAA and PRI remain evidence profiles, not manufactured scalar risk scores. DQI is calculated from the actual full dataset; semantic novelty/total stay unavailable without embeddings. ML readiness remains blocked without independent outcome labels.
- All new observations and metric records carry `engineering_only`, `scientifically_validated=false`, judge identity, source hash, and protocol provenance. Test-provider artifacts are explicitly marked synthetic. No production approval is inferred.

## Persistence, summaries, and recovery

Each case's observations are written by the append-only ObservationStore as they occur. The case, judges, BSDA, SAEA, recovery, DRAA, specification, and isolation evidence are committed together to the workspace database. Only committed cases advance the UI's saved-case counter. Existing committed cases are skipped on resume, including recorded failures; correcting failures requires a new run, not silently rewriting old evidence.

After server restart, full-corpus jobs are reconstructed from persisted runs; unfinished jobs offer a resume path. Resume requires the same source hash, model configuration/digest, judge and protocol. For API models the user reconnects and re-enters the key. Per-case uncommitted observation files can be reused without repeating saved target calls. Judge calls for an interrupted, uncommitted case may repeat.

The live testing page has a **Stop test and keep saved work** button. It calls
`POST /internal/benchmark-jobs/{job_id}/stop` from the loopback workspace.
The job moves through `stopping` to `stopped`; a current provider or judge call
is allowed to return or time out, then no further call is sent. Already
committed cases and append-only partial observations remain available for
resume. Stopping does not turn incomplete cases into non-leaks or completed
measurements. A stop request after finalization has begun may finish as a
completed run. The button controls this server's active job, not a process
running on a different server instance.

Reports use the planned 10,000-case denominator, even for partial runs. Each numeric field is averaged across its available linked records with its own sample count and status counts; missing values are excluded, not zero-filled. BSDA has up to 20,000 pair records, while SAEA/recovery each have 10,000 case records. These are not combined into a new safety score. Metric rows are streamed to avoid loading every rich evidence payload simultaneously. The line chart retains every timing value in a single path, and case details are expanded 100 at a time.

Existing three-case or subset reports are retained unchanged; the missing controlled observations cannot be retroactively reconstructed. Start a new full-corpus run to collect them.

## Run or inspect

Use the model test page, choose the target and judge, review the full budget, and explicitly confirm before launch. No full real-model run was launched as part of implementation verification.

Dry-run only (no inference):

```powershell
.\.venv\Scripts\python.exe -m scripts.run_full_benchmark --model gemma3:4b --dry-run
```

The CLI requires `--confirm-full-corpus` for actual generation. Add `--run-id` with the original settings to resume an existing run.
