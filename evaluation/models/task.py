"""Benchmark Task and Dataset Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskCategory(str, Enum):
    RESEARCH = "research"
    PLANNER = "planner"
    TOOL_SELECTION = "tool_selection"
    BROWSER = "browser"
    LLM_ROUTING = "llm_routing"
    REFLECTION = "reflection"
    LEARNING = "learning"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    MULTI_AGENT = "multi_agent"
    DATA_INTELLIGENCE = "data_intelligence"
    DECISION_INTELLIGENCE = "decision_intelligence"
    CONNECTORS = "connectors"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    RELIABILITY = "reliability"


class TaskDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTREME = "extreme"


@dataclass
class GoldenAnswer:
    """Ground truth reference data for automated validation."""

    expected_output: Optional[Any] = None
    expected_keywords: List[str] = field(default_factory=list)
    forbidden_keywords: List[str] = field(default_factory=list)
    expected_tool_calls: List[str] = field(default_factory=list)
    expected_status_code: int = 200
    min_citations_required: int = 0
    max_allowed_latency_ms: float = 10000.0
    assertion_rules: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expected_output": self.expected_output,
            "expected_keywords": self.expected_keywords,
            "forbidden_keywords": self.forbidden_keywords,
            "expected_tool_calls": self.expected_tool_calls,
            "expected_status_code": self.expected_status_code,
            "min_citations_required": self.min_citations_required,
            "max_allowed_latency_ms": self.max_allowed_latency_ms,
            "assertion_rules": self.assertion_rules,
        }


@dataclass
class BenchmarkTask:
    """Represents a single standardized evaluation benchmark task."""

    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    category: TaskCategory = TaskCategory.RESEARCH
    difficulty: TaskDifficulty = TaskDifficulty.MEDIUM
    input_prompt: str = ""
    context_data: Dict[str, Any] = field(default_factory=dict)
    golden_answer: GoldenAnswer = field(default_factory=GoldenAnswer)
    tags: List[str] = field(default_factory=list)
    timeout_seconds: float = 30.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "input_prompt": self.input_prompt,
            "context_data": self.context_data,
            "golden_answer": self.golden_answer.to_dict(),
            "tags": self.tags,
            "timeout_seconds": self.timeout_seconds,
        }
