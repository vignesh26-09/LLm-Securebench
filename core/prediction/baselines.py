"""Deterministic Phase 9B engineering baselines, with no post-hoc calibration."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from core.prediction.models import CalibrationStatus


@dataclass(frozen=True, slots=True)
class PredictionOutput:
    raw_score: float
    model_probability_estimate: float | None
    calibration_status: CalibrationStatus = CalibrationStatus.NOT_CALIBRATED


@dataclass(frozen=True, slots=True)
class PrevalenceBaseline:
    prevalence: float
    training_class_count: int

    @classmethod
    def fit(cls, labels: Sequence[int]) -> "PrevalenceBaseline":
        if not labels or any(label not in (0, 1) for label in labels):
            raise ValueError("prevalence baseline requires non-empty binary training labels")
        return cls(sum(labels) / len(labels), len(set(labels)))

    def predict(self, rows: Sequence[Sequence[float]]) -> tuple[PredictionOutput, ...]:
        return tuple(PredictionOutput(self.prevalence, self.prevalence) for _ in rows)


@dataclass(frozen=True, slots=True)
class LogisticRegressionConfig:
    max_iterations: int
    learning_rate: float
    l2_regularization: float

    def __post_init__(self) -> None:
        if self.max_iterations <= 0 or self.learning_rate <= 0 or self.l2_regularization < 0:
            raise ValueError("logistic regression configuration must be positive (L2 may be zero)")


@dataclass(frozen=True, slots=True)
class LogisticRegressionBaseline:
    coefficients: tuple[float, ...]
    intercept: float
    config: LogisticRegressionConfig

    @classmethod
    def fit(cls, rows: Sequence[Sequence[float]], labels: Sequence[int], config: LogisticRegressionConfig) -> "LogisticRegressionBaseline":
        if not rows or len(rows) != len(labels) or any(label not in (0, 1) for label in labels):
            raise ValueError("logistic regression requires aligned non-empty binary training data")
        if len(set(labels)) < 2:
            raise ValueError("logistic regression requires two training classes")
        width = len(rows[0])
        if width == 0 or any(len(row) != width for row in rows):
            raise ValueError("feature rows must be non-empty and equal width")
        weights = [0.0] * width
        intercept = 0.0
        count = float(len(rows))
        for _ in range(config.max_iterations):
            gradients = [0.0] * width
            intercept_gradient = 0.0
            for row, label in zip(rows, labels, strict=True):
                probability = _sigmoid(intercept + sum(weight * value for weight, value in zip(weights, row, strict=True)))
                error = probability - label
                intercept_gradient += error
                for index, value in enumerate(row):
                    gradients[index] += error * value
            for index in range(width):
                gradients[index] = gradients[index] / count + config.l2_regularization * weights[index]
                weights[index] -= config.learning_rate * gradients[index]
            intercept -= config.learning_rate * intercept_gradient / count
        return cls(tuple(weights), intercept, config)

    def predict(self, rows: Sequence[Sequence[float]]) -> tuple[PredictionOutput, ...]:
        if any(len(row) != len(self.coefficients) for row in rows):
            raise ValueError("feature width does not match fitted logistic model")
        return tuple(PredictionOutput(_sigmoid(self.intercept + sum(weight * value for weight, value in zip(self.coefficients, row, strict=True))), _sigmoid(self.intercept + sum(weight * value for weight, value in zip(self.coefficients, row, strict=True)))) for row in rows)


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponent = math.exp(value)
    return exponent / (1.0 + exponent)
