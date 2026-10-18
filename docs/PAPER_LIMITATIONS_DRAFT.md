# Limitations Draft

The current evidence supports a traceable evaluation system and one
judge-comparison calibration analysis; it does not establish a validated
automated substitute for independent human safety labels. The calibration
result is limited to the persisted JailbreakBench source revision, the fixed
predeclared mapping, and the current Gemma-based judge configuration. Its
coverage and agreement values should not be generalized to other datasets,
judges, prompting protocols, models, or label definitions.

The local Qwen/Gemma record is an engineering demonstration with two
configurations, four runs, and 12 evaluations. It contains no human-labelled
model comparison and no experimental design that supports ranking, percentage
differences, attack-success rates, or claims about relative model safety.

Several metric families are deliberately retained as exploratory or
uncalibrated. Layer 1 detector signals are not ground truth. BSDA has no
validated composite; RC is raw and calibration-dependent; SAEA's observed
cumulative vulnerability is not ASR and candidate Bliss analysis is
experimental; DRAA Modes A/B are diagnostic and uncalibrated while Mode C is
unavailable; PRI has no validated scalar grade; and DQI is exploratory. The
ML path lacks production labels and validated predictive performance, and the
available statistics infrastructure does not justify inferential claims.

Consequently, the paper should present SecureLLMBench as a framework for
evidence-aware measurement and reproducible artifact handling. Claims about
security effectiveness, human-equivalent judging, calibrated risk, model
rankings, predictive ML, or broad generalization require future studies with
predefined labels, suitable experimental samples, and independent validation.
