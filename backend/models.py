from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


@dataclass(frozen=True)
class Evidence:
    page: int
    text: str
    score: float = 0.0


@dataclass
class DocumentAnalysis:
    title: str
    summary: str
    requirements: list[Evidence] = field(default_factory=list)
    dates: list[Evidence] = field(default_factory=list)
    conditions: list[Evidence] = field(default_factory=list)
    exclusions: list[Evidence] = field(default_factory=list)
    alerts: list[Evidence] = field(default_factory=list)


@dataclass
class AgentAnswer:
    answer: str
    evidence: list[Evidence]
    found: bool


@dataclass(frozen=True)
class ScreeningCriterion:
    identifier: str
    text: str
    page: int
    terms: tuple[str, ...]


@dataclass(frozen=True)
class CriterionMatch:
    criterion: ScreeningCriterion
    coverage: float
    status: str
    matched_terms: tuple[str, ...]
    cv_evidence: Evidence | None = None


@dataclass
class CandidateReview:
    filename: str
    score: int
    matches: list[CriterionMatch] = field(default_factory=list)


@dataclass
class CriteriaExtraction:
    criteria: list[ScreeningCriterion] = field(default_factory=list)
    excluded_sensitive: list[Evidence] = field(default_factory=list)
