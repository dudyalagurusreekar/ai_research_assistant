"""OrchestrationPlanner — integrates IntelligentPlanningEngine with IntelligentLLMOrchestrator and PromptManager."""

from typing import Dict, Any, List, Optional
from core.planner.engine import IntelligentPlanningEngine
from core.planner.models.context import PlannerContext
from core.orchestration.orchestrator import IntelligentLLMOrchestrator
from core.prompts.manager import prompt_manager
from utils.logger import get_logger

logger = get_logger("OrchestrationPlanner")


class OrchestrationPlanner:
    """Unified planning and reasoning facade."""

    def __init__(
        self,
        planning_engine: Optional[IntelligentPlanningEngine] = None,
        llm_orchestrator: Optional[IntelligentLLMOrchestrator] = None,
    ):
        self.planning_engine = planning_engine or IntelligentPlanningEngine()
        self.llm_orchestrator = llm_orchestrator or IntelligentLLMOrchestrator()

    def create_plan(
        self,
        query: str,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
    ) -> PlannerContext:
        """Deconstruct user query, generate DAG execution waves, and select optimal tools."""
        logger.info(f"Generating orchestration plan for query: '{query[:80]}...'")
        
        # 1. Render system planner prompt
        planner_prompt = prompt_manager.render("system_planner", {"query": query})
        
        # 2. Execute 10-stage planning engine
        ctx = self.planning_engine.plan(
            query=query,
            available_tools=available_tools,
            session_id=session_id,
        )
        
        # 3. Store rendered prompt in metadata
        if not hasattr(ctx, "metadata") or ctx.metadata is None:
            ctx.metadata = {}
        ctx.metadata["rendered_prompt"] = planner_prompt
        
        return ctx


orchestration_planner = OrchestrationPlanner()
