"""ContinuousLearningEngine facade orchestrating experience store, pattern analyzer, strategy optimizer, and feedback."""

from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from core.learning.models.context import (
    ExperienceRecord,
    ExperienceOutcome,
    StrategyRecommendation,
    PatternInsight,
)
from core.learning.components.experience_store import ExperienceStore
from core.learning.components.tool_performance_db import ToolPerformanceDatabase
from core.learning.components.provider_performance_db import ProviderPerformanceDatabase
from core.learning.components.pattern_analyzer import PatternAnalyzer
from core.learning.components.strategy_optimizer import StrategyOptimizer
from core.learning.components.feedback_interface import PlannerFeedbackInterface

logger = get_logger("ContinuousLearningEngine")


class ContinuousLearningEngine:
    """Main facade for ARA v2.0 Sprint 5 Continuous Learning and Experience Engine."""

    def __init__(self, storage_dir: Optional[str] = None):
        self.store = ExperienceStore(storage_dir=storage_dir)
        self.tool_db = ToolPerformanceDatabase(storage_dir=storage_dir)
        self.provider_db = ProviderPerformanceDatabase(storage_dir=storage_dir)
        self.pattern_analyzer = PatternAnalyzer(self.store)
        self.strategy_optimizer = StrategyOptimizer(
            self.store, self.pattern_analyzer, self.tool_db, self.provider_db
        )
        self.feedback_interface = PlannerFeedbackInterface(
            self.store, self.tool_db, self.provider_db
        )
        self.enabled = True

    def consult_experience(
        self, query: str, intent: Optional[str] = None, candidate_tools: Optional[List[str]] = None
    ) -> StrategyRecommendation:
        """Consults the Experience Engine to obtain strategy recommendations before planning."""
        if not self.enabled:
            return StrategyRecommendation(query=query, intent=intent)

        return self.strategy_optimizer.recommend_strategy(query, intent=intent, candidate_tools=candidate_tools)

    def record_experience(
        self,
        query: str,
        intent: str,
        complexity_score: int,
        selected_tools: List[str],
        excluded_tools: List[str],
        dag_nodes_count: int,
        dag_edges_count: int,
        parallel_waves: int,
        execution_latency_ms: float,
        total_tokens_used: int = 0,
        total_cost_usd: float = 0.0,
        providers_used: Optional[List[str]] = None,
        outcome: ExperienceOutcome = ExperienceOutcome.SUCCESS,
        verification_confidence: float = 1.0,
        reflection_actions: Optional[List[str]] = None,
        error_logs: Optional[List[str]] = None,
        tool_telemetry: Optional[List[Dict[str, Any]]] = None,
        provider_telemetry: Optional[List[Dict[str, Any]]] = None,
    ) -> ExperienceRecord:
        """Records completed workflow execution feedback into the experience engine."""
        if not self.enabled:
            return ExperienceRecord(query=query, intent=intent)

        return self.feedback_interface.record_workflow_execution(
            query=query,
            intent=intent,
            complexity_score=complexity_score,
            selected_tools=selected_tools,
            excluded_tools=excluded_tools,
            dag_nodes_count=dag_nodes_count,
            dag_edges_count=dag_edges_count,
            parallel_waves=parallel_waves,
            execution_latency_ms=execution_latency_ms,
            total_tokens_used=total_tokens_used,
            total_cost_usd=total_cost_usd,
            providers_used=providers_used,
            outcome=outcome,
            verification_confidence=verification_confidence,
            reflection_actions=reflection_actions,
            error_logs=error_logs,
            tool_telemetry=tool_telemetry,
            provider_telemetry=provider_telemetry,
        )

    def clear_learning_data(self) -> None:
        """Clears all historical experience records and performance databases (reversibility)."""
        self.store.clear()
        self.tool_db.clear()
        self.provider_db.clear()
        logger.info("Continuous learning data cleared.")

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Returns aggregated summary metrics across stored experience."""
        total_records = self.store.count()
        records = self.store.list_records()
        successes = sum(1 for r in records if r.outcome == ExperienceOutcome.SUCCESS)
        rate = (successes / total_records) if total_records > 0 else 0.0

        return {
            "total_experiences": total_records,
            "successful_experiences": successes,
            "overall_success_rate": round(rate, 4),
            "tool_count": len(self.tool_db._metrics),
            "provider_count": len(self.provider_db._metrics),
            "learning_enabled": self.enabled,
        }
