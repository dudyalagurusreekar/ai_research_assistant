"""Optimization Advisor generating non-intrusive system recommendations from benchmark evaluation telemetry."""

from typing import Dict, Any, List
from tools.benchmark.interfaces.benchmark_interfaces import IOptimizationAdvisor
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    BenchmarkReportModel,
    OptimizationRecommendation,
)
from infrastructure.logging.logger import StructuredLogger


class OptimizationAdvisor(IOptimizationAdvisor):
    """Analyzes benchmark results and failure taxonomy to generate targeted optimization recommendations without mutating system architecture."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("OptimizationAdvisor")

    def analyze_and_recommend(
        self, report: BenchmarkReportModel
    ) -> List[OptimizationRecommendation]:
        """Analyze benchmark evaluation report and return actionable optimization recommendations."""
        recommendations: List[OptimizationRecommendation] = []
        breakdown = report.error_breakdown or {}

        # 1. Check planning & tool selection errors
        if breakdown.get("planning", 0) > 0 or breakdown.get("tool_selection", 0) > 0:
            recommendations.append(
                OptimizationRecommendation(
                    category="workflow_strategy",
                    recommendation="Refine TaskPlanner prompt decomposition and enforce pre-step tool validation.",
                    reason=f"Detected {breakdown.get('planning', 0) + breakdown.get('tool_selection', 0)} planning/tool-selection errors.",
                    priority="high",
                    scope="orchestrator",
                )
            )

        # 2. Check browser errors
        if breakdown.get("browser", 0) > 0:
            recommendations.append(
                OptimizationRecommendation(
                    category="browser_recovery",
                    recommendation="Enable DOM auto-wait retries and captcha recovery heuristics in Browser Platform.",
                    reason=f"Detected {breakdown.get('browser', 0)} browser navigation failures.",
                    priority="high",
                    scope="browser_platform",
                )
            )

        # 3. Check search errors
        if breakdown.get("search", 0) > 0:
            recommendations.append(
                OptimizationRecommendation(
                    category="search_improvements",
                    recommendation="Enhance search query expansion and enable multi-engine fallback.",
                    reason=f"Detected {breakdown.get('search', 0)} search retrieval misses.",
                    priority="medium",
                    scope="search_platform",
                )
            )

        # 4. Check vision / OCR errors
        if breakdown.get("vision", 0) > 0 or breakdown.get("ocr", 0) > 0:
            recommendations.append(
                OptimizationRecommendation(
                    category="vision_preprocessing",
                    recommendation="Apply image contrast enhancement and crop multi-modal bounding boxes before vision model inference.",
                    reason=f"Detected {breakdown.get('vision', 0) + breakdown.get('ocr', 0)} vision/OCR errors.",
                    priority="medium",
                    scope="vision_platform",
                )
            )

        # 5. Check formatting errors
        if breakdown.get("formatting", 0) > 0:
            recommendations.append(
                OptimizationRecommendation(
                    category="prompt_refinement",
                    recommendation="Update system instructions to strictly output final answer in GAIA concise schema.",
                    reason=f"Detected {breakdown.get('formatting', 0)} formatting validation failures.",
                    priority="high",
                    scope="prompts",
                )
            )

        # 6. Check verification & code execution errors
        if breakdown.get("code_execution", 0) > 0 or breakdown.get("verification", 0) > 0:
            recommendations.append(
                OptimizationRecommendation(
                    category="additional_verification",
                    recommendation="Add Python sandbox sanity checks and post-execution verification loop.",
                    reason=f"Detected {breakdown.get('code_execution', 0) + breakdown.get('verification', 0)} code execution/verification errors.",
                    priority="medium",
                    scope="code_platform",
                )
            )

        # Default fallback recommendation if 100% accurate
        if not recommendations:
            recommendations.append(
                OptimizationRecommendation(
                    category="performance_tuning",
                    recommendation="Maintain async subagent execution tuning and proactive context pruner caching.",
                    reason="Suite executed with high accuracy. Focus on latency and cost optimization.",
                    priority="low",
                    scope="global",
                )
            )

        self._logger.info(f"Generated {len(recommendations)} optimization recommendations.")
        return recommendations

    def get_optimized_params(self, task: GAIATask) -> Dict[str, Any]:
        """Return task execution parameters based on difficulty level and category."""
        params = {
            "retry_limit": 3,
            "verification_enabled": True,
            "temperature": 0.0,
            "max_tool_iterations": 10,
        }

        lvl_str = task.level.value if hasattr(task.level, "value") else str(task.level)
        if lvl_str == "level_3":
            params["max_tool_iterations"] = 20
            params["retry_limit"] = 5
            params["timeout_seconds"] = 600
        elif lvl_str == "level_2":
            params["max_tool_iterations"] = 15
            params["retry_limit"] = 4

        return params


# Alias for backward compatibility
OptimizationManager = OptimizationAdvisor
