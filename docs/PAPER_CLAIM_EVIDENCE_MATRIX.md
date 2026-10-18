# Paper Claim–Evidence Matrix

| ID | Proposed paper claim | Evidence | Status | Required wording / restriction |
|---|---|---|---|---|
| C1 | SecureLLMBench records traceable evaluation artifacts. | Table 1; implementation and paper-trace artifacts. | Engineering-supported | Say “implements” or “records”; do not claim it validates outcomes. |
| C2 | The framework exposes evidence status and blocks unsupported scientific presentation. | Table 1; Figure 3; readiness records. | Engineering-supported | Describe guardrails as implementation behavior. |
| C3 | The persisted JailbreakBench calibration has N=300, usable N=295, 98.333% coverage, 53.898% raw agreement, and kappa 0.211261. | Table 2; `calibration_verification.json`; results JSON. | Empirical | Keep the dataset revision, checksum, mapping, and sample sizes with the result. |
| C4 | The current Gemma judge cannot replace independent human outcome labels. | C3 and the documented protocol interpretation. | Empirical, conservative | State this only for the current judge and fixed predeclared mapping. |
| C5 | Two local models completed a small engineering demonstration. | Table 3 and local trace artifacts. | Engineering-supported | Report two configurations, four runs, 12 evaluations, and 36 Layer 1 records. |
| C6 | BSDA, RC, SAEA, DRAA, PRI, DQI, ML, and statistics components exist with distinct readiness states. | Table 1; Table 3; Figure 3. | Engineering / exploratory | Never merge readiness states into a scientific performance claim. |
| C7 | Local Layer 1 outputs establish safety, attack success, or risk. | No qualifying evidence. | Blocked | Do not make this claim. |
| C8 | The local demonstration compares Qwen and Gemma safety. | No qualifying evidence. | Blocked | Do not make this claim or imply a winner. |
| C9 | The ML component predicts outcomes or generalizes to LLM safety. | No production labels or validated predictive result. | Blocked | Describe only as implemented infrastructure. |
| C10 | Further human-labelled validation can test judge suitability. | Protocol and limitations documentation. | Future validation | Use future tense; do not state that validation occurred. |

## Evidence-status vocabulary

- **Engineering-supported:** an implementation or trace exists; it does not
  establish a scientific outcome.
- **Empirical:** a value was computed from the cited persisted artifact under
  the documented configuration.
- **Exploratory / uncalibrated:** an implemented output may be inspected but
  cannot support a validated scientific conclusion.
- **Blocked:** no paper result may be asserted from the currently available
  evidence.
- **Future validation:** an allowed proposal for later work, not a completed
  study.
