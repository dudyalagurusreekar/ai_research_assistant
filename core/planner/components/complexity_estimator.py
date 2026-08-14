"""ComplexityEstimator — estimates request complexity, cost, and resources.

Uses intent, query analysis signals, and heuristic rules to predict how many
steps, tool calls, tokens, and seconds a request will likely require.
"""

from __future__ import annotations

from core.planner.interfaces.base import IComplexityEstimator
from core.planner.models.context import ComplexityEstimate, PlannerContext, QueryIntent
from infrastructure.logging.logger import StructuredLogger


# ---------------------------------------------------------------------------
# Base cost profiles per intent
# ---------------------------------------------------------------------------

_INTENT_PROFILES = {
    QueryIntent.FACTUAL_QA: {"score": 2, "steps": 2, "tools": 1, "tokens": 1000, "latency": 10.0},
    QueryIntent.COMPARISON: {"score": 5, "steps": 5, "tools": 2, "tokens": 3000, "latency": 30.0},
    QueryIntent.DOCUMENT_ANALYSIS: {"score": 4, "steps": 3, "tools": 2, "tokens": 4000, "latency": 25.0},
    QueryIntent.CODE_EXECUTION: {"score": 3, "steps": 2, "tools": 1, "tokens": 1500, "latency": 15.0},
    QueryIntent.VISION_ANALYSIS: {"score": 4, "steps": 3, "tools": 2, "tokens": 2000, "latency": 20.0},
    QueryIntent.MULTI_STEP_RESEARCH: {"score": 7, "steps": 6, "tools": 3, "tokens": 5000, "latency": 60.0},
    QueryIntent.AMBIGUOUS: {"score": 3, "steps": 3, "tools": 2, "tokens": 2000, "latency": 20.0},
    QueryIntent.MEMORY_OPERATION: {"score": 1, "steps": 1, "tools": 1, "tokens": 500, "latency": 5.0},
    QueryIntent.REPORT_GENERATION: {"score": 5, "steps": 4, "tools": 2, "tokens": 3500, "latency": 30.0},
}


class ComplexityEstimator(IComplexityEstimator):
    """Heuristic complexity estimator driven by intent profiles and query signals."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ComplexityEstimator")

    @property
    def component_name(self) -> str:
        return "ComplexityEstimator"

    def estimate(self, ctx: PlannerContext) -> ComplexityEstimate:
        """Produce a complexity estimate adjusted by query-specific signals."""
        intent = ctx.intent or QueryIntent.AMBIGUOUS
        profile = _INTENT_PROFILES.get(intent, _INTENT_PROFILES[QueryIntent.AMBIGUOUS])

        score = profile["score"]
        steps = profile["steps"]
        tools = profile["tools"]
        tokens = profile["tokens"]
        latency = profile["latency"]

        # Adjustments based on query analysis
        analysis = ctx.query_analysis
        if analysis:
            # Multi-source queries increase complexity
            if analysis.source_count_hint > 1:
                multiplier = min(analysis.source_count_hint, 5)
                score = min(10, score + multiplier - 1)
                steps += multiplier - 1
                tools += 1
                tokens += 1000 * (multiplier - 1)
                latency += 15.0 * (multiplier - 1)

            # File references add document processing overhead
            if analysis.has_file_reference:
                steps += 1
                tokens += 2000
                latency += 20.0

            # URL references add browsing overhead
            if analysis.has_url_reference:
                steps += 1
                tokens += 1000
                latency += 15.0

            # High ambiguity adds exploratory steps
            if analysis.ambiguity_score > 0.5:
                steps += 1
                score = min(10, score + 1)

        # Compute max step limit (always at least the estimated steps + margin)
        max_step_limit = max(steps + 3, 10)

        reasons = []
        reasons.append(f"Base profile for intent '{intent.value}'")
        if analysis and analysis.source_count_hint > 1:
            reasons.append(f"multi-source ({analysis.source_count_hint} sources)")
        if analysis and analysis.has_file_reference:
            reasons.append("document processing required")
        if analysis and analysis.has_url_reference:
            reasons.append("web browsing required")

        estimate = ComplexityEstimate(
            score=min(10, score),
            estimated_steps=steps,
            estimated_tool_calls=tools,
            estimated_tokens=tokens,
            estimated_latency_seconds=latency,
            max_step_limit=min(max_step_limit, 20),
            reasoning="; ".join(reasons),
        )

        ctx.complexity = estimate
        ctx.add_trace(
            stage="complexity_estimation",
            message=f"Complexity score={estimate.score}/10, "
                    f"steps={estimate.estimated_steps}, latency={estimate.estimated_latency_seconds:.0f}s",
            data={
                "score": estimate.score,
                "steps": estimate.estimated_steps,
                "tools": estimate.estimated_tool_calls,
                "tokens": estimate.estimated_tokens,
                "max_step_limit": estimate.max_step_limit,
            },
        )
        self._logger.info(
            f"Complexity estimated: score={estimate.score}, steps={estimate.estimated_steps}"
        )
        return estimate
