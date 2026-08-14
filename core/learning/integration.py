"""Integration layer for ARA v2.0 Continuous Learning Engine."""

from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from core.learning.engine import ContinuousLearningEngine
from core.learning.models.context import StrategyRecommendation

logger = get_logger("LearningIntegration")

_global_learning_engine: Optional[ContinuousLearningEngine] = None


def get_learning_engine() -> ContinuousLearningEngine:
    """Returns singleton instance of ContinuousLearningEngine."""
    global _global_learning_engine
    if _global_learning_engine is None:
        _global_learning_engine = ContinuousLearningEngine()
    return _global_learning_engine


def reset_learning_engine() -> None:
    """Resets global learning engine singleton instance."""
    global _global_learning_engine
    _global_learning_engine = None


class LearningIntegrationAdapter:
    """Adapter facilitating seamless integration between Learning Engine and Planner / Agent runtimes."""

    def __init__(self, engine: Optional[ContinuousLearningEngine] = None):
        self.engine = engine or get_learning_engine()

    def enhance_planner_context(self, context: Any) -> None:
        """Injects strategy recommendations directly into PlannerContext prior to ToolSelector stage."""
        if not hasattr(context, "query") or not context.query:
            return

        intent_val = context.intent.value if hasattr(context, "intent") and context.intent else None
        rec: StrategyRecommendation = self.engine.consult_experience(
            query=context.query, intent=intent_val
        )

        # Store recommendation inside context metadata dictionary
        if hasattr(context, "metadata"):
            context.metadata["strategy_recommendation"] = rec
            logger.info(f"Enhanced PlannerContext with strategy recommendation (confidence={rec.confidence:.2f})")

    def record_agent_run_completion(
        self,
        query: str,
        response: str,
        latency_s: float,
        intent: str = "general_qa",
        selected_tools: Optional[List[str]] = None,
        success: bool = True,
    ) -> None:
        """Records completed agent execution into the experience engine."""
        if selected_tools is None:
            selected_tools = ["python_interpreter"]

        self.engine.record_experience(
            query=query,
            intent=intent,
            complexity_score=5,
            selected_tools=selected_tools,
            excluded_tools=[],
            dag_nodes_count=len(selected_tools),
            dag_edges_count=max(0, len(selected_tools) - 1),
            parallel_waves=1,
            execution_latency_ms=latency_s * 1000.0,
            total_tokens_used=100,
            total_cost_usd=0.0001,
            providers_used=["gemini/gemini-3-flash-preview"],
            outcome="success" if success else "failure",
            verification_confidence=1.0 if success else 0.0,
        )
