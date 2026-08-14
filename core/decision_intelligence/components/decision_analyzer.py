"""Decision Analyzer Component — Identifies objectives, constraints, criteria, and context."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.objective import (
    ComparisonOperator,
    Constraint,
    ConstraintType,
    DecisionContext,
    Objective,
    ObjectiveType,
)
from utils.logger import get_logger

logger = get_logger("DecisionAnalyzer")


class DecisionAnalyzer:
    """Component responsible for identifying objectives, constraints, and framing context."""

    def __init__(self) -> None:
        pass

    def analyze_context(
        self,
        query: str,
        topic: str = "",
        domain: str = "general",
        explicit_objectives: Optional[List[Objective]] = None,
        explicit_constraints: Optional[List[Constraint]] = None,
        context_data: Optional[Dict[str, Any]] = None,
        risk_tolerance: float = 0.5,
        urgency_level: str = "medium",
    ) -> DecisionContext:
        """Parse raw query and context to synthesize structured DecisionContext."""
        logger.info(f"Analyzing decision context for query: '{query[:60]}...'")
        context_data = context_data or {}
        objectives: List[Objective] = list(explicit_objectives or [])
        constraints: List[Constraint] = list(explicit_constraints or [])

        # 1. Automatic objective extraction if not explicitly provided
        if not objectives:
            objectives = self._extract_default_objectives(query, domain)

        # 2. Automatic constraint extraction
        extracted_constraints = self._extract_constraints_from_query(query)
        for c in extracted_constraints:
            if not any(existing.name == c.name for existing in constraints):
                constraints.append(c)

        # Ensure default constraints if none found
        if not constraints:
            constraints.append(
                Constraint(
                    name="Implementation Feasibility",
                    description="Option must be technically realizable within standard operational bounds.",
                    constraint_type=ConstraintType.HARD,
                    metric="feasibility_score",
                    threshold_value=0.5,
                    operator=ComparisonOperator.GREATER_THAN_OR_EQUAL,
                )
            )

        # 3. Create context object
        context = DecisionContext(
            topic=topic or self._infer_topic(query),
            domain=domain,
            user_query=query,
            target_audience=context_data.get("target_audience", "stakeholders"),
            objectives=objectives,
            constraints=constraints,
            urgency_level=urgency_level,
            risk_tolerance=risk_tolerance,
        )

        logger.info(
            f"DecisionContext created with {len(context.objectives)} objectives and {len(context.constraints)} constraints."
        )
        return context

    def _extract_default_objectives(self, query: str, domain: str) -> List[Objective]:
        """Generate default standard objectives based on domain and text cues."""
        objectives: List[Objective] = []
        q_lower = query.lower()

        # Performance / Latency
        if any(w in q_lower for w in ["performance", "speed", "latency", "throughput", "fast"]):
            objectives.append(
                Objective(
                    name="Performance & Speed",
                    description="Maximize system responsiveness and execution throughput.",
                    category=ObjectiveType.TECHNICAL,
                    weight=0.3,
                    target_direction="MAXIMIZE",
                )
            )

        # Cost / Financial
        if any(w in q_lower for w in ["cost", "budget", "cheap", "price", "financial", "roi"]):
            objectives.append(
                Objective(
                    name="Cost Efficiency",
                    description="Minimize total cost of ownership (TCO) and operational expense.",
                    category=ObjectiveType.FINANCIAL,
                    weight=0.3,
                    target_direction="MINIMIZE",
                )
            )

        # Scalability / Reliability
        if any(w in q_lower for w in ["scale", "scalability", "reliability", "availability", "uptime"]):
            objectives.append(
                Objective(
                    name="Scalability & Reliability",
                    description="Maximize fault tolerance and horizontal scale capacity.",
                    category=ObjectiveType.OPERATIONAL,
                    weight=0.25,
                    target_direction="MAXIMIZE",
                )
            )

        # Default fallback set if nothing matched specifically
        if not objectives:
            objectives = [
                Objective(
                    name="Technical Capability & Quality",
                    description="Maximize functional capability, accuracy, and architectural quality.",
                    category=ObjectiveType.TECHNICAL,
                    weight=0.4,
                    target_direction="MAXIMIZE",
                ),
                Objective(
                    name="Cost & Resource Efficiency",
                    description="Minimize resource footprint, licensing, and operational overhead.",
                    category=ObjectiveType.FINANCIAL,
                    weight=0.3,
                    target_direction="MINIMIZE",
                ),
                Objective(
                    name="Operational Simplicity & Maintainability",
                    description="Maximize developer velocity, ease of maintenance, and ecosystem support.",
                    category=ObjectiveType.OPERATIONAL,
                    weight=0.3,
                    target_direction="MAXIMIZE",
                ),
            ]

        # Normalize weights so sum = 1.0
        total_weight = sum(o.weight for o in objectives)
        if total_weight > 0:
            for o in objectives:
                o.weight = round(o.weight / total_weight, 3)

        return objectives

    def _extract_constraints_from_query(self, query: str) -> List[Constraint]:
        """Parse regex patterns for budget, latency, uptime, or complexity constraints."""
        constraints: List[Constraint] = []
        q_lower = query.lower()

        # Budget match (e.g., "budget under $5000", "cost < 1000", "$5000 USD")
        budget_match = re.search(r"(?:budget|cost|price)\s*(?:of|under|less than|<|is|max)?\s*\$?([0-9,]+)", q_lower)
        if not budget_match:
            budget_match = re.search(r"\$([0-9,]+)", q_lower)

        if budget_match:
            try:
                val = float(budget_match.group(1).replace(",", ""))
                constraints.append(
                    Constraint(
                        name="Maximum Budget Constraint",
                        description=f"Estimated cost must not exceed ${val:,.2f}",
                        constraint_type=ConstraintType.HARD,
                        metric="estimated_cost",
                        threshold_value=val,
                        operator=ComparisonOperator.LESS_THAN_OR_EQUAL,
                        unit="USD",
                    )
                )
            except ValueError:
                pass

        # Latency match (e.g., "< 100ms", "latency under 200 milliseconds")
        latency_match = re.search(r"(?:latency|response time)\s*(?:under|less than|<|is|max)?\s*([0-9]+)\s*(?:ms|milliseconds)", q_lower)
        if latency_match:
            try:
                val = float(latency_match.group(1))
                constraints.append(
                    Constraint(
                        name="Maximum Latency Constraint",
                        description=f"Response latency must be less than {val} ms",
                        constraint_type=ConstraintType.HARD,
                        metric="latency_ms",
                        threshold_value=val,
                        operator=ComparisonOperator.LESS_THAN_OR_EQUAL,
                        unit="ms",
                    )
                )
            except ValueError:
                pass

        return constraints

    def _infer_topic(self, query: str) -> str:
        """Infer topic summary from user query."""
        words = query.strip().split()
        if len(words) <= 6:
            return query
        return " ".join(words[:6]) + "..."
