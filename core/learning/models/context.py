"""Data models for ARA v2.0 Continuous Learning & Experience Engine."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime, timezone
import uuid


class ExperienceOutcome(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass
class ToolPerformanceMetrics:
    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    reliability_score: float = 1.0  # 0.0 to 1.0
    context_efficiency: float = 1.0  # ratio of useful outputs
    last_error_type: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def update(self, success: bool, latency_ms: float, error_type: Optional[str] = None):
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error_type:
                self.last_error_type = error_type
        
        self.total_latency_ms += latency_ms
        self.avg_latency_ms = self.total_latency_ms / self.total_calls
        self.reliability_score = self.successful_calls / self.total_calls
        self.last_updated = datetime.now(timezone.utc).isoformat()


@dataclass
class ProviderPerformanceMetrics:
    provider_id: str  # e.g., 'gemini/gemini-2.5-flash'
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limit_count: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    reliability_score: float = 1.0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def update(self, success: bool, latency_ms: float, tokens: int = 0, cost_usd: float = 0.0, is_rate_limit: bool = False):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        if is_rate_limit:
            self.rate_limit_count += 1
            
        self.total_tokens += tokens
        self.total_cost_usd += cost_usd
        self.avg_latency_ms = ((self.avg_latency_ms * (self.total_requests - 1)) + latency_ms) / self.total_requests
        self.reliability_score = self.successful_requests / self.total_requests
        self.last_updated = datetime.now(timezone.utc).isoformat()


@dataclass
class PatternInsight:
    pattern_id: str
    intent: str
    sample_count: int
    optimal_tools: List[str]
    suggested_wave_count: int
    avg_success_rate: float
    common_failure_modes: List[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class StrategyRecommendation:
    query: str
    intent: Optional[str]
    recommended_tools: List[str] = field(default_factory=list)
    excluded_tools: List[str] = field(default_factory=list)
    preferred_providers: List[str] = field(default_factory=list)
    recommended_max_waves: int = 2
    estimated_complexity: int = 5
    historical_success_probability: float = 1.0
    risk_warnings: List[str] = field(default_factory=list)
    insight_summary: str = ""
    confidence: float = 0.0


@dataclass
class ExperienceRecord:
    record_id: str = field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:12]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    query: str = ""
    intent: str = "general_qa"
    complexity_score: int = 5
    planner_decisions: Dict[str, Any] = field(default_factory=dict)
    selected_tools: List[str] = field(default_factory=list)
    excluded_tools: List[str] = field(default_factory=list)
    dag_nodes_count: int = 1
    dag_edges_count: int = 0
    parallel_waves: int = 1
    execution_latency_ms: float = 0.0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    providers_used: List[str] = field(default_factory=list)
    outcome: ExperienceOutcome = ExperienceOutcome.SUCCESS
    verification_confidence: float = 1.0
    reflection_actions: List[str] = field(default_factory=list)
    error_logs: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "query": self.query,
            "intent": self.intent,
            "complexity_score": self.complexity_score,
            "planner_decisions": self.planner_decisions,
            "selected_tools": self.selected_tools,
            "excluded_tools": self.excluded_tools,
            "dag_nodes_count": self.dag_nodes_count,
            "dag_edges_count": self.dag_edges_count,
            "parallel_waves": self.parallel_waves,
            "execution_latency_ms": self.execution_latency_ms,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": self.total_cost_usd,
            "providers_used": self.providers_used,
            "outcome": self.outcome.value if isinstance(self.outcome, ExperienceOutcome) else str(self.outcome),
            "verification_confidence": self.verification_confidence,
            "reflection_actions": self.reflection_actions,
            "error_logs": self.error_logs,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperienceRecord":
        outcome_val = data.get("outcome", "success")
        try:
            outcome_enum = ExperienceOutcome(outcome_val)
        except ValueError:
            outcome_enum = ExperienceOutcome.SUCCESS

        return cls(
            record_id=data.get("record_id", f"exp_{uuid.uuid4().hex[:12]}"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            query=data.get("query", ""),
            intent=data.get("intent", "general_qa"),
            complexity_score=data.get("complexity_score", 5),
            planner_decisions=data.get("planner_decisions", {}),
            selected_tools=data.get("selected_tools", []),
            excluded_tools=data.get("excluded_tools", []),
            dag_nodes_count=data.get("dag_nodes_count", 1),
            dag_edges_count=data.get("dag_edges_count", 0),
            parallel_waves=data.get("parallel_waves", 1),
            execution_latency_ms=data.get("execution_latency_ms", 0.0),
            total_tokens_used=data.get("total_tokens_used", 0),
            total_cost_usd=data.get("total_cost_usd", 0.0),
            providers_used=data.get("providers_used", []),
            outcome=outcome_enum,
            verification_confidence=data.get("verification_confidence", 1.0),
            reflection_actions=data.get("reflection_actions", []),
            error_logs=data.get("error_logs", []),
            tags=data.get("tags", []),
        )
