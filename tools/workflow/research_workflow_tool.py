"""Research Workflow Tool — Autonomous Research Engine Tool Facade for ToolRegistry."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.workflow.engine import AutonomousResearchEngine
from utils.logger import get_logger

logger = get_logger("ResearchWorkflowTool")


class ResearchWorkflowTool:
    """Tool Registry interface for executing autonomous research workflows."""

    def __init__(self, engine: Optional[AutonomousResearchEngine] = None) -> None:
        self.engine = engine or AutonomousResearchEngine()
        self.name = "research_workflow_tool"
        self.description = "Executes autonomous multi-stage research workflows, question generation, evidence aggregation, and report composition."

    def execute(self, action: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute tool action."""
        logger.info(f"ResearchWorkflowTool executing action '{action}'")

        if action == "execute_research":
            query = kwargs.get("query", "Default Autonomous Research Query")
            ctx = self.engine.execute_autonomous_research(query)
            return {
                "status": "success",
                "session_id": ctx.session_id,
                "stage": ctx.stage.value,
                "report_summary": ctx.report.executive_summary if ctx.report else "",
                "markdown_content": ctx.report.markdown_content if ctx.report else "",
                "questions_resolved": ctx.metrics.questions_resolved,
                "total_latency_ms": ctx.metrics.total_latency_ms,
            }

        elif action == "generate_questions":
            query = kwargs.get("query", "Query")
            goal = self.engine.goal_analyzer.analyze_goal(query)
            questions = self.engine.question_generator.generate_questions(goal)
            return {
                "status": "success",
                "goal": goal.to_dict(),
                "questions": [q.to_dict() for q in questions],
            }

        elif action == "compose_report":
            query = kwargs.get("query", "Report Query")
            goal = self.engine.goal_analyzer.analyze_goal(query)
            questions = self.engine.question_generator.generate_questions(goal)
            report = self.engine.report_composer.compose_report(goal, questions, [], [], [])
            return {
                "status": "success",
                "title": report.title,
                "markdown_content": report.markdown_content,
            }

        else:
            return {"status": "error", "message": f"Unsupported action '{action}'"}
