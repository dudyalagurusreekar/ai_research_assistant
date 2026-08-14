"""PlannerFeedbackInterface for recording execution telemetry, reflection events, and outcomes."""

from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from core.learning.models.context import ExperienceRecord, ExperienceOutcome
from core.learning.components.experience_store import ExperienceStore
from core.learning.components.tool_performance_db import ToolPerformanceDatabase
from core.learning.components.provider_performance_db import ProviderPerformanceDatabase

logger = get_logger("PlannerFeedbackInterface")


class PlannerFeedbackInterface:
    """Interface connecting agent/planner runtime execution back into the Experience Engine."""

    def __init__(
        self,
        experience_store: ExperienceStore,
        tool_db: ToolPerformanceDatabase,
        provider_db: ProviderPerformanceDatabase,
    ):
        self.store = experience_store
        self.tool_db = tool_db
        self.provider_db = provider_db

    def record_workflow_execution(
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
        """Records a completed workflow execution into the Experience Engine."""
        if providers_used is None:
            providers_used = []
        if reflection_actions is None:
            reflection_actions = []
        if error_logs is None:
            error_logs = []

        record = ExperienceRecord(
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
        )

        self.store.add_record(record)

        # Update per-tool performance database
        if tool_telemetry:
            for tt in tool_telemetry:
                self.tool_db.record_tool_call(
                    tool_name=tt.get("tool_name", "unknown"),
                    success=tt.get("success", True),
                    latency_ms=tt.get("latency_ms", 0.0),
                    error_type=tt.get("error_type"),
                )
        else:
            is_success = (outcome == ExperienceOutcome.SUCCESS)
            per_tool_latency = execution_latency_ms / max(1, len(selected_tools))
            for t_name in selected_tools:
                self.tool_db.record_tool_call(
                    tool_name=t_name,
                    success=is_success,
                    latency_ms=per_tool_latency,
                    error_type=error_logs[0] if error_logs else None,
                )

        # Update per-provider performance database
        if provider_telemetry:
            for pt in provider_telemetry:
                self.provider_db.record_request(
                    provider_id=pt.get("provider_id", "default_llm"),
                    success=pt.get("success", True),
                    latency_ms=pt.get("latency_ms", 0.0),
                    tokens=pt.get("tokens", 0),
                    cost_usd=pt.get("cost_usd", 0.0),
                    is_rate_limit=pt.get("is_rate_limit", False),
                )
        elif providers_used:
            is_success = (outcome == ExperienceOutcome.SUCCESS)
            per_prov_tokens = total_tokens_used // max(1, len(providers_used))
            per_prov_cost = total_cost_usd / max(1, len(providers_used))
            for pid in providers_used:
                self.provider_db.record_request(
                    provider_id=pid,
                    success=is_success,
                    latency_ms=execution_latency_ms,
                    tokens=per_prov_tokens,
                    cost_usd=per_prov_cost,
                )

        logger.info(f"Recorded workflow feedback for record_id={record.record_id} (outcome={record.outcome.value})")
        return record
