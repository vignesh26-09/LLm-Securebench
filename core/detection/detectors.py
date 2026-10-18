"""Configurable deterministic Layer 1 regex, keyword, and token-pattern detectors."""

import re
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from core.detection.models import DetectorResult


@dataclass(frozen=True, slots=True)
class RegexRule:
    name: str
    pattern: str
    score: float
    signal_scores: Mapping[str, float] = field(default_factory=dict)
    flags: int = re.IGNORECASE


@dataclass(frozen=True, slots=True)
class KeywordRule:
    name: str
    keyword: str
    score: float
    signal_scores: Mapping[str, float] = field(default_factory=dict)
    case_sensitive: bool = False


@dataclass(frozen=True, slots=True)
class PatternRule:
    """Matches a set of required terms, optionally preserving their specified order."""
    name: str
    required_terms: tuple[str, ...]
    score: float
    signal_scores: Mapping[str, float] = field(default_factory=dict)
    ordered: bool = False
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        if not self.required_terms or any(not term for term in self.required_terms):
            raise ValueError("PatternRule requires at least one non-empty term")


class RegexDetector:
    name = "regex"

    def __init__(self, rules: Sequence[RegexRule]) -> None:
        self._rules = tuple(rules)
        self._compiled = tuple((rule, re.compile(rule.pattern, rule.flags)) for rule in self._rules)

    def detect(self, text: str) -> DetectorResult:
        matches: list[tuple[RegexRule, str]] = []
        for rule, pattern in self._compiled:
            matches.extend((rule, match.group(0)) for match in pattern.finditer(text))
        return _result(self.name, matches, len(self._rules))


class KeywordDetector:
    name = "keyword"

    def __init__(self, rules: Sequence[KeywordRule]) -> None:
        self._rules = tuple(rules)

    def detect(self, text: str) -> DetectorResult:
        matches: list[tuple[KeywordRule, str]] = []
        folded = text.casefold()
        for rule in self._rules:
            candidate = rule.keyword if rule.case_sensitive else rule.keyword.casefold()
            haystack = text if rule.case_sensitive else folded
            if candidate in haystack:
                matches.append((rule, rule.keyword))
        return _result(self.name, matches, len(self._rules))


class PatternDetector:
    name = "pattern"

    def __init__(self, rules: Sequence[PatternRule]) -> None:
        self._rules = tuple(rules)

    def detect(self, text: str) -> DetectorResult:
        matches: list[tuple[PatternRule, str]] = []
        for rule in self._rules:
            haystack = text if rule.case_sensitive else text.casefold()
            terms = rule.required_terms if rule.case_sensitive else tuple(term.casefold() for term in rule.required_terms)
            positions = [haystack.find(term) for term in terms]
            if all(position >= 0 for position in positions) and (not rule.ordered or positions == sorted(positions)):
                matches.append((rule, " + ".join(rule.required_terms)))
        return _result(self.name, matches, len(self._rules))


def _result(detector_name: str, matches: Sequence[tuple[object, str]], rule_count: int) -> DetectorResult:
    score = max((rule.score for rule, _ in matches), default=0.0)
    signals: dict[str, float] = {}
    for rule, _ in matches:
        for name, value in rule.signal_scores.items():
            signals[name] = max(signals.get(name, 0.0), value)
    evidence = tuple(evidence for _, evidence in matches)
    confidence = min(1.0, len(matches) / rule_count) if rule_count else None
    return DetectorResult(detector_name, score, evidence, confidence, signals, {"matched_rule_count": len(matches), "rule_count": rule_count})
