"""Evaluation Models — Real-World Evaluation Suite task definitions, scoring rubrics, and result containers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class EvaluationRubricCategory(Enum):
    """Rubric evaluation categories across all 10 Real-World Tasks."""

    PLANNING_QUALITY = "Planning quality"
    TOOL_SELECTION = "Tool selection"
    SOURCE_QUALITY = "Source quality"
    EVIDENCE_VERIFICATION = "Evidence verification"
    REFLECTION = "Reflection"
    REPORT_STRUCTURE = "Report structure"
    CITATION_ACCURACY = "Citation accuracy"
    HALLUCINATION_RATE = "Hallucination rate"
    LATENCY = "Latency"
    OVERALL_USEFULNESS = "Overall usefulness"


class ScoreGrade(Enum):
    """Evaluation score grades."""

    EXCELLENT = "Excellent"
    GOOD = "Good"
    ACCEPTABLE = "Acceptable"
    NEEDS_IMPROVEMENT = "Needs Improvement"


@dataclass
class CategoryScore:
    """Score for a specific rubric category."""

    category: EvaluationRubricCategory
    grade: ScoreGrade = ScoreGrade.EXCELLENT
    score_points: float = 10.0  # max 10.0
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "grade": self.grade.value,
            "score": self.score_points,
            "rationale": self.rationale,
        }


@dataclass
class EvaluationTaskSpec:
    """Specification for a Real-World Evaluation Suite task."""

    task_id: str
    task_number: int
    title: str
    prompt: str
    domain: str
    tested_capabilities: List[str]
    expected_sections: List[str]
    output_filename: str


@dataclass
class TaskEvaluationResult:
    """Execution and scoring result for a single real-world task."""

    task_spec: EvaluationTaskSpec
    status: str = "completed"
    report_markdown: str = ""
    report_file_path: str = ""
    artifact_path: str = ""
    latency_ms: float = 0.0
    category_scores: Dict[EvaluationRubricCategory, CategoryScore] = field(default_factory=dict)
    total_score: float = 0.0
    max_possible_score: float = 100.0
    citations_count: int = 0
    conflicts_analyzed: int = 0
    subsystems_exercised: List[str] = field(default_factory=list)
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_total_score(self) -> float:
        self.total_score = sum(cs.score_points for cs in self.category_scores.values())
        return self.total_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_spec.task_id,
            "task_number": self.task_spec.task_number,
            "title": self.task_spec.title,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "total_score": self.compute_total_score(),
            "max_possible_score": self.max_possible_score,
            "citations_count": self.citations_count,
            "conflicts_analyzed": self.conflicts_analyzed,
            "subsystems_exercised": self.subsystems_exercised,
            "report_file_path": self.report_file_path,
            "category_scores": {k.value: v.to_dict() for k, v in self.category_scores.items()},
        }


@dataclass
class RealWorldSuiteResult:
    """Master suite evaluation scorecard and result collection."""

    suite_id: str = field(default_factory=lambda: f"eval_suite_{uuid.uuid4().hex[:8]}")
    results: List[TaskEvaluationResult] = field(default_factory=list)
    total_score: float = 0.0
    max_score: float = 1000.0
    average_score: float = 0.0
    total_latency_ms: float = 0.0
    all_passed: bool = True
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def aggregate_metrics(self) -> None:
        self.total_score = sum(r.compute_total_score() for r in self.results)
        self.max_score = len(self.results) * 100.0
        self.average_score = self.total_score / len(self.results) if self.results else 0.0
        self.total_latency_ms = sum(r.latency_ms for r in self.results)
        self.all_passed = all(r.status == "completed" and r.compute_total_score() >= 90.0 for r in self.results)

    def to_dict(self) -> Dict[str, Any]:
        self.aggregate_metrics()
        return {
            "suite_id": self.suite_id,
            "total_tasks": len(self.results),
            "total_score": self.total_score,
            "max_score": self.max_score,
            "average_score": self.average_score,
            "total_latency_ms": self.total_latency_ms,
            "all_passed": self.all_passed,
            "tasks": [r.to_dict() for r in self.results],
        }
