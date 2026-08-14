"""Research Goal Analyzer — Deconstructs raw user queries into structured ResearchGoal specs."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from core.workflow.models.goal import ConstraintSpec, GoalDomain, GoalPriority, ResearchGoal
from utils.logger import get_logger

logger = get_logger("ResearchGoalAnalyzer")


class ResearchGoalAnalyzer:
    """Analyzes raw research queries and extracts domain, primary objectives, key entities, and constraints."""

    def __init__(self) -> None:
        self._domain_keywords = {
            GoalDomain.COMPUTER_SCIENCE: ["ai", "llm", "code", "algorithm", "model", "transformer", "agent", "gpu"],
            GoalDomain.BIOMEDICAL: ["clinical", "gene", "protein", "disease", "drug", "trial", "medical"],
            GoalDomain.FINANCE: ["stock", "market", "portfolio", "trading", "crypto", "revenue", "price"],
            GoalDomain.DATA_ANALYTICS: ["dataset", "dataframe", "chart", "statistic", "clustering", "regression"],
            GoalDomain.ENGINEERING: ["robotics", "hardware", "circuit", "control", "power", "design"],
        }

    def analyze_goal(self, raw_query: str, constraints_override: Optional[Dict[str, Any]] = None) -> ResearchGoal:
        """Deconstruct raw user query into structured ResearchGoal."""
        query_lower = raw_query.lower()

        # 1. Infer GoalDomain
        domain = GoalDomain.GENERAL_SCIENCE
        for dom, keywords in self._domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                domain = dom
                break

        # 2. Extract Primary Objectives & Entities
        objectives: List[str] = []
        if "compare" in query_lower:
            objectives.append("Compare technical benchmarks and performance trade-offs.")
        if "benchmark" in query_lower or "evaluat" in query_lower:
            objectives.append("Analyze quantitative benchmark metrics and empirical accuracy.")
        if "code" in query_lower or "implement" in query_lower:
            objectives.append("Develop and verify sandboxed algorithmic code implementation.")
        if not objectives:
            objectives.append("Synthesize comprehensive literature and empirical findings.")

        entities = [w.title() for w in re.findall(r"\b[A-Z][a-zA-Z0-9_\-\.]{2,}\b", raw_query)]

        # 3. Formulate ConstraintSpec
        constraints = ConstraintSpec()
        if constraints_override:
            if "max_execution_time_seconds" in constraints_override:
                constraints.max_execution_time_seconds = float(constraints_override["max_execution_time_seconds"])
            if "preferred_format" in constraints_override:
                constraints.preferred_format = str(constraints_override["preferred_format"])

        goal = ResearchGoal(
            raw_query=raw_query,
            title=raw_query[:60].strip(),
            domain=domain,
            priority=GoalPriority.HIGH if "critical" in query_lower else GoalPriority.NORMAL,
            primary_objectives=objectives,
            key_entities=entities,
            constraints=constraints,
        )

        logger.info(f"ResearchGoalAnalyzer deconstructed goal '{goal.title}' [Domain: {domain.value}]")
        return goal
