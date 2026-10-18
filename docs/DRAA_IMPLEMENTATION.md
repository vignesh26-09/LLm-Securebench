# DRAA Mode A/B implementation

SecureLLMBench implements provider-neutral DRAA **Mode A** lossless evidence
extraction and **Mode B** uncalibrated descriptive diagnostics in `core/draa`.
Every `DRAAEvidenceRecord` has `status = uncalibrated` and `risk_score = null`.
It is not a safety-failure probability or scalar security-risk estimate.

## Evidence record and adapters

The immutable record preserves case/attack/run/sequence/model/dataset/threat
identity, schema version, severity as a separate field, features, warnings,
errors, and source provenance. `EvidenceFeature` accepts scalar or structured
JSON-compatible values, source-native units/orientation, status/reason,
upstream confidence/CI/SE/bootstrap interval, failure information, and provider,
model, prompt, rubric, calibration, and artifact metadata where supplied.

- Layer 1 keeps each detector result and report signals as detector-native
  evidence; it does not label attack success.
- Layer 2 keeps each judge dimension, its status/confidence/uncertainty and full
  provider/prompt/rubric provenance. Judge scores remain measurements.
- BSDA keeps semantic, safety, instruction, and structural components separately.
  It reuses raw/normalized values and calibration/CI metadata; no DRAA BSDA
  composite is created.
- RC accepts a source payload and retains its raw/bounded/terminal fields and
  status exactly. It never computes a recovery-to-risk inversion.
- SAEA retains `CV_obs` and SI separately plus one structured diagnostic entry
  for per-step context effects, order effects, Shapley values, and recovery
  trends. Undefined SI remains undefined.
- Severity is retained separately and never multiplied by a probability.

## Status, provenance, and diagnostics

Status explicitly distinguishes applicable, not applicable, uncalibrated,
undefined, failed, skipped, refused, insufficient data, incompatible, and
absent. No state is encoded as `NaN` or numeric zero. JSON serialization is
deterministic and round-trips enums/statuses/provenance.

Mode B supplies only source coverage, status counts, uncertainty availability,
and nullable correlation-ready numeric series. It does not calculate correlations
as a DRAA decision, remove features, normalize values, or apply dependence
correction.

`DRAACalibrationArtifact` is a future data contract for methodology/label and
upstream versions, feature contracts, reference population, learned model
parameters, policies, coverage/splits, and validation provenance. It neither
fits nor applies a predictor.

## What DRAA Does Not Yet Do

- no scalar risk probability or Mode C prediction;
- no arbitrary or equal weights, `R_fast`, or `R_beh`;
- no Bayesian posterior, priors, or likelihoods;
- no severity multiplication;
- no automatic dependence correction or feature removal;
- no learned calibration, normalization, RC inversion, SAEA scalarization, or
  missing-value imputation.

The future blocker remains a calibrated, threat-model-scoped label definition,
compatible calibration artifact, learned/validated model, and validation plan.
