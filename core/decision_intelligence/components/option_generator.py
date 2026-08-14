"""Option Generator Component — Generates, structures, and validates candidate decision options."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.objective import ComparisonOperator, Constraint, ConstraintType, DecisionContext
from core.decision_intelligence.models.option import (
    FeasibilityAssessment,
    Option,
    OptionStatus,
    ResourceRequirement,
)
from utils.logger import get_logger

logger = get_logger("OptionGenerator")


class OptionGenerator:
    """Component responsible for synthesizing and evaluating option feasibility."""

    def __init__(self) -> None:
        pass

    def generate_options(
        self,
        context: DecisionContext,
        preset_options: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Option]:
        """Generate candidate options and evaluate feasibility against context constraints."""
        logger.info(f"Generating decision options for context: '{context.topic}'")
        options: List[Option] = []

        if preset_options:
            for p in preset_options:
                opt = Option(
                    title=p.get("title", "Preset Option"),
                    description=p.get("description", ""),
                    category=p.get("category", "general"),
                    pros=p.get("pros", []),
                    cons=p.get("cons", []),
                    estimated_cost=float(p.get("estimated_cost", 0.0)),
                    implementation_complexity=p.get("implementation_complexity", "medium"),
                    time_to_value_days=int(p.get("time_to_value_days", 30)),
                    metadata=p.get("metadata", {}),
                )
                options.append(opt)
        else:
            options = self._synthesize_default_options(context)

        # Validate each option against hard and soft constraints
        for opt in options:
            self._evaluate_feasibility(opt, context.constraints)

        logger.info(
            f"Generated {len(options)} options ({sum(1 for o in options if o.status == OptionStatus.FEASIBLE)} feasible)."
        )
        return options

    def _synthesize_default_options(self, context: DecisionContext) -> List[Option]:
        """Synthesize candidate options based on domain/topic heuristics."""
        q_lower = context.user_query.lower()

        # Database / Storage domain
        if any(w in q_lower for w in ["database", "db", "postgres", "mongo", "sql"]):
            return [
                Option(
                    title="Managed Relational Database (PostgreSQL)",
                    description="Deploy a fully managed ACID-compliant relational DB with high consistency.",
                    category="Database",
                    pros=["Strong consistency", "Rich SQL querying", "Widespread ecosystem support"],
                    cons=["Higher cost at scale", "Schema migration overhead"],
                    estimated_cost=1200.0,
                    implementation_complexity="medium",
                    time_to_value_days=14,
                ),
                Option(
                    title="Distributed Document Store (MongoDB / DynamoDB)",
                    description="Utilize a flexible, schema-less NoSQL database designed for rapid horizontal scale.",
                    category="Database",
                    pros=["Flexible schema", "Seamless horizontal scale", "Low operational effort"],
                    cons=["Eventual consistency tradeoffs", "Complex multi-document transactions"],
                    estimated_cost=850.0,
                    implementation_complexity="low",
                    time_to_value_days=7,
                ),
                Option(
                    title="Hybrid Polyglot Persistence Architecture",
                    description="Combine Relational DB for core transactional data and Key-Value Cache for high-throughput reads.",
                    category="Database",
                    pros=["Optimal performance per workload", "Flexible data modeling"],
                    cons=["Increased operational complexity", "Dual write sync management"],
                    estimated_cost=2100.0,
                    implementation_complexity="high",
                    time_to_value_days=30,
                ),
            ]

        # Cloud / Architecture domain
        if any(w in q_lower for w in ["cloud", "aws", "gcp", "azure", "kubernetes", "k8s", "microservice", "architecture"]):
            return [
                Option(
                    title="Option A: Fully Managed Cloud Native Serverless",
                    description="Leverage managed cloud services (Lambdas, Cloud Run) for zero idle cost and auto-scaling.",
                    category="Architecture",
                    pros=["Low maintenance", "Pay-per-use cost structure", "Automatic scaling"],
                    cons=["Potential cold start latency", "Vendor lock-in"],
                    estimated_cost=500.0,
                    implementation_complexity="low",
                    time_to_value_days=10,
                ),
                Option(
                    title="Option B: Containerized Kubernetes Cluster",
                    description="Deploy workload in a managed Kubernetes cluster with full multi-cloud portability.",
                    category="Architecture",
                    pros=["High control", "Multi-cloud portability", "Standardized container deployment"],
                    cons=["Higher base infrastructure cost", "Cluster maintenance complexity"],
                    estimated_cost=2500.0,
                    implementation_complexity="high",
                    time_to_value_days=25,
                ),
                Option(
                    title="Option C: Modular Monolith on Virtual Machines",
                    description="Consolidate services into a well-structured modular monolith on auto-scaling instance groups.",
                    category="Architecture",
                    pros=["Simple deployment pipeline", "Low network latency between modules", "Ease of debugging"],
                    cons=["Single point of scaling", "Tight coupling risk if unmonitored"],
                    estimated_cost=1100.0,
                    implementation_complexity="medium",
                    time_to_value_days=14,
                ),
            ]

        # General domain fallback
        return [
            Option(
                title="Option 1: Recommended Production Solution",
                description="Modern, balanced solution optimizing quality, stability, and total cost of ownership.",
                category="Strategy",
                pros=["Proven industry track record", "Strong documentation and ecosystem support"],
                cons=["Standard licensing or hosting costs"],
                estimated_cost=1500.0,
                implementation_complexity="medium",
                time_to_value_days=15,
            ),
            Option(
                title="Option 2: Lean / High-Velocity Alternative",
                description="Streamlined solution prioritizing rapid delivery and minimal initial resource investment.",
                category="Strategy",
                pros=["Fast time to value", "Lower upfront capital cost"],
                cons=["May require refactoring at extreme scale"],
                estimated_cost=600.0,
                implementation_complexity="low",
                time_to_value_days=7,
            ),
            Option(
                title="Option 3: Enterprise Custom-Engineered Architecture",
                description="Custom high-throughput architecture engineered for maximum performance and strict compliance.",
                category="Strategy",
                pros=["Complete customization", "Zero third-party vendor lock-in", "Maximum security control"],
                cons=["Highest initial development cost and time-to-market"],
                estimated_cost=4500.0,
                implementation_complexity="high",
                time_to_value_days=45,
            ),
        ]

    def _evaluate_feasibility(self, option: Option, constraints: List[Constraint]) -> None:
        """Check hard and soft constraints against option attributes."""
        assessment = FeasibilityAssessment()
        is_feasible = True

        for c in constraints:
            passed, note = self._check_constraint(option, c)
            if passed:
                if c.constraint_type == ConstraintType.HARD:
                    assessment.hard_constraints_passed.append(c.name)
            else:
                if c.constraint_type == ConstraintType.HARD:
                    is_feasible = False
                    assessment.hard_constraints_failed.append(c.name)
                    assessment.violation_notes.append(f"HARD constraint '{c.name}' failed: {note}")
                else:
                    assessment.soft_constraint_violations.append(c.name)
                    assessment.violation_notes.append(f"SOFT constraint '{c.name}' violated: {note}")

        assessment.is_feasible = is_feasible
        if not is_feasible:
            assessment.status = OptionStatus.INFEASIBLE
            option.status = OptionStatus.INFEASIBLE
        elif assessment.soft_constraint_violations:
            assessment.status = OptionStatus.CONDITIONAL
            option.status = OptionStatus.CONDITIONAL
        else:
            assessment.status = OptionStatus.FEASIBLE
            option.status = OptionStatus.FEASIBLE

        option.feasibility = assessment

    def _check_constraint(self, option: Option, constraint: Constraint) -> tuple[bool, str]:
        """Check if option satisfies a single metric constraint."""
        val = getattr(option, constraint.metric, None)
        if val is None and isinstance(option.metadata, dict):
            val = option.metadata.get(constraint.metric)

        if val is None:
            return True, "Metric value not present for option"

        t_val = constraint.threshold_value
        op = constraint.operator

        if op == ComparisonOperator.LESS_THAN_OR_EQUAL:
            satisfied = float(val) <= float(t_val)
            return satisfied, f"{val} <= {t_val}"
        elif op == ComparisonOperator.GREATER_THAN_OR_EQUAL:
            satisfied = float(val) >= float(t_val)
            return satisfied, f"{val} >= {t_val}"
        elif op == ComparisonOperator.EQUAL:
            satisfied = str(val) == str(t_val)
            return satisfied, f"{val} == {t_val}"
        elif op == ComparisonOperator.NOT_EQUAL:
            satisfied = str(val) != str(t_val)
            return satisfied, f"{val} != {t_val}"
        elif op == ComparisonOperator.CONTAINS:
            satisfied = str(t_val).lower() in str(val).lower()
            return satisfied, f"'{t_val}' in '{val}'"

        return True, "Unknown operator"
