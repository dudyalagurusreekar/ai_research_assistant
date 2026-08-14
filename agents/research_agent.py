from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from agents.runtime import SafeCodeAgent

from config import get_model, get_research_agent_config
from tools import registry
from core.planner.engine import IntelligentPlanningEngine
from core.planner.integration import AgentPlannerIntegration
from core.planner.models.context import PlannerContext

# Path to the compact prompt template (80% smaller than the smolagents default)
_COMPACT_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "compact_code_agent.yaml"


def _load_compact_prompts() -> dict:
    """Load the compact prompt templates from YAML."""
    return yaml.safe_load(_COMPACT_PROMPT_PATH.read_text(encoding="utf-8"))


def _build_tool_metadata(tools: list) -> List[Dict[str, Any]]:
    """Extract metadata dicts from smolagents tool instances for the planner."""
    metadata: List[Dict[str, Any]] = []
    for tool in tools:
        name = getattr(tool, "name", None) or type(tool).__name__
        desc = getattr(tool, "description", "") or ""
        metadata.append({
            "name": name,
            "description": desc,
            "capabilities": [name],
        })
    return metadata


class ResearchAgent:
    """
    Builds and manages the Research CodeAgent with v2.0 Intelligent Planning.
    """

    def __init__(self):
        self.config = get_research_agent_config()
        self.model = get_model()
        self.tools = registry.get_tools()
        self._planner_integration = AgentPlannerIntegration()
        self._tool_metadata = _build_tool_metadata(self.tools)

    def build(self) -> SafeCodeAgent:
        """Build a SafeCodeAgent (backward-compatible, no planning injection)."""
        return SafeCodeAgent(
            model=self.model,
            tools=self.tools,
            prompt_templates=_load_compact_prompts(),
            max_steps=self.config.max_steps,
            planning_interval=self.config.planning_interval,
            additional_authorized_imports=self.config.authorized_imports,
            stream_outputs=self.config.stream_outputs,
            use_structured_outputs_internally=self.config.use_structured_outputs_internally,
            max_print_outputs_length=self.config.max_print_outputs_length,
        )

    def plan(self, query: str) -> PlannerContext:
        """Run the Intelligent Planning Engine on a query and return the plan."""
        return self._planner_integration.plan_for_agent(
            query=query,
            available_tools=self._tool_metadata,
        )

    def build_with_plan(self, plan_ctx: PlannerContext) -> SafeCodeAgent:
        """Build a SafeCodeAgent with planning hints injected into its prompt."""
        prompts = _load_compact_prompts()

        # Inject planning hints into the system prompt
        plan_hint = self._planner_integration.get_prompt_hint(plan_ctx)
        if plan_hint and "system_prompt" in prompts:
            prompts["system_prompt"] += f"\n\n{plan_hint}\n"

        # Use the planner's constraint-driven max_steps if available
        max_steps = self.config.max_steps
        if plan_ctx.constraints and plan_ctx.constraints.max_steps:
            max_steps = plan_ctx.constraints.max_steps

        return SafeCodeAgent(
            model=self.model,
            tools=self.tools,
            prompt_templates=prompts,
            max_steps=max_steps,
            planning_interval=self.config.planning_interval,
            additional_authorized_imports=self.config.authorized_imports,
            stream_outputs=self.config.stream_outputs,
            use_structured_outputs_internally=self.config.use_structured_outputs_internally,
            max_print_outputs_length=self.config.max_print_outputs_length,
        )

    def plan_and_run(self, query: str) -> Any:
        """Plan the query, build an agent with planning context, and execute."""
        plan_ctx = self.plan(query)
        agent = self.build_with_plan(plan_ctx)
        return agent.run(query)


def create_agent() -> SafeCodeAgent:
    """
    Backward-compatible factory — returns a plain agent without planning injection.
    """
    return ResearchAgent().build()