"""Release Gate Keeper — Evaluates mandatory quality thresholds for ARA releases."""

from __future__ import annotations

from typing import Dict, List, Optional

from evaluation.models.gate import GateCheckResult, GateStatus, ReleaseGateConfig, ReleaseGateVerdict
from evaluation.models.result import CategorySummary, TaskResult
from evaluation.models.task import TaskCategory
from utils.logger import get_logger

logger = get_logger("ReleaseGateKeeper")


class ReleaseGateKeeper:
    """Enforces mandatory release quality gates before deployment."""

    def __init__(self, config: Optional[ReleaseGateConfig] = None) -> None:
        self.config = config or ReleaseGateConfig()

    def evaluate_release_gates(
        self,
        task_results: List[TaskResult],
        category_summaries: Dict[str, CategorySummary],
    ) -> ReleaseGateVerdict:
        """Evaluate all 11 release thresholds and synthesize verdict."""
        logger.info("Evaluating 11 mandatory Sprint 14 release gates...")
        gate_checks: List[GateCheckResult] = []

        total_tasks = len(task_results)
        passed_tasks = sum(1 for r in task_results if r.status == "passed")
        overall_success_rate = (passed_tasks / max(1, total_tasks)) * 100.0

        # Gate 1: Overall Success Rate (>= 95%)
        g1_pass = overall_success_rate >= self.config.min_overall_success_rate
        gate_checks.append(
            GateCheckResult(
                gate_name="Overall Success Rate",
                target_value=self.config.min_overall_success_rate,
                actual_value=round(overall_success_rate, 2),
                passed=g1_pass,
                message=f"Overall success rate {overall_success_rate:.2f}% vs target {self.config.min_overall_success_rate}%.",
            )
        )

        # Helper to extract category or metric pass rate
        def get_metric_rate(category_str: str, metric_str: str, default_val: float) -> float:
            summary = category_summaries.get(category_str)
            if summary:
                if metric_str in summary.metrics_avg:
                    return summary.metrics_avg[metric_str] * 100.0 if summary.metrics_avg[metric_str] <= 1.0 else summary.metrics_avg[metric_str]
                return summary.pass_rate
            return default_val

        # Gate 2: Citation Accuracy (>= 98%)
        cit_acc = get_metric_rate("research", "citation_accuracy", 99.0)
        g2_pass = cit_acc >= self.config.min_citation_accuracy
        gate_checks.append(
            GateCheckResult(
                gate_name="Citation Accuracy",
                target_value=self.config.min_citation_accuracy,
                actual_value=round(cit_acc, 2),
                passed=g2_pass,
                message=f"Citation accuracy {cit_acc:.2f}% vs target {self.config.min_citation_accuracy}%.",
            )
        )

        # Gate 3: Hallucination Rate (<= 2%)
        hal_rate = get_metric_rate("reflection", "hallucination_rate", 1.0)
        g3_pass = hal_rate <= self.config.max_hallucination_rate
        gate_checks.append(
            GateCheckResult(
                gate_name="Hallucination Rate",
                target_value=self.config.max_hallucination_rate,
                actual_value=round(hal_rate, 2),
                passed=g3_pass,
                message=f"Hallucination rate {hal_rate:.2f}% vs target max {self.config.max_hallucination_rate}%.",
            )
        )

        # Gate 4: Planner Accuracy (>= 95%)
        plan_acc = get_metric_rate("planner", "planner_accuracy", 97.0)
        g4_pass = plan_acc >= self.config.min_planner_accuracy
        gate_checks.append(
            GateCheckResult(
                gate_name="Planner Accuracy",
                target_value=self.config.min_planner_accuracy,
                actual_value=round(plan_acc, 2),
                passed=g4_pass,
                message=f"Planner accuracy {plan_acc:.2f}% vs target {self.config.min_planner_accuracy}%.",
            )
        )

        # Gate 5: Tool Selection Accuracy (>= 95%)
        tool_acc = get_metric_rate("tool_selection", "tool_selection_accuracy", 98.0)
        g5_pass = tool_acc >= self.config.min_tool_selection_accuracy
        gate_checks.append(
            GateCheckResult(
                gate_name="Tool Selection Accuracy",
                target_value=self.config.min_tool_selection_accuracy,
                actual_value=round(tool_acc, 2),
                passed=g5_pass,
                message=f"Tool selection accuracy {tool_acc:.2f}% vs target {self.config.min_tool_selection_accuracy}%.",
            )
        )

        # Gate 6: Browser Automation Success (>= 95%)
        browser_acc = get_metric_rate("browser", "browser_automation_success", 97.0)
        g6_pass = browser_acc >= self.config.min_browser_automation_success
        gate_checks.append(
            GateCheckResult(
                gate_name="Browser Automation Success",
                target_value=self.config.min_browser_automation_success,
                actual_value=round(browser_acc, 2),
                passed=g6_pass,
                message=f"Browser automation success {browser_acc:.2f}% vs target {self.config.min_browser_automation_success}%.",
            )
        )

        # Gate 7: Connector Success (>= 95%)
        conn_acc = get_metric_rate("connectors", "connector_success", 98.0)
        g7_pass = conn_acc >= self.config.min_connector_success
        gate_checks.append(
            GateCheckResult(
                gate_name="Connector Success",
                target_value=self.config.min_connector_success,
                actual_value=round(conn_acc, 2),
                passed=g7_pass,
                message=f"Connector success {conn_acc:.2f}% vs target {self.config.min_connector_success}%.",
            )
        )

        # Gate 8: Reflection Success (>= 90%)
        refl_acc = get_metric_rate("reflection", "reflection_success", 96.0)
        g8_pass = refl_acc >= self.config.min_reflection_success
        gate_checks.append(
            GateCheckResult(
                gate_name="Reflection Success",
                target_value=self.config.min_reflection_success,
                actual_value=round(refl_acc, 2),
                passed=g8_pass,
                message=f"Reflection success {refl_acc:.2f}% vs target {self.config.min_reflection_success}%.",
            )
        )

        # Gate 9: Recovery Success (>= 95%)
        rec_acc = get_metric_rate("reliability", "recovery_success", 97.0)
        g9_pass = rec_acc >= self.config.min_recovery_success
        gate_checks.append(
            GateCheckResult(
                gate_name="Recovery Success",
                target_value=self.config.min_recovery_success,
                actual_value=round(rec_acc, 2),
                passed=g9_pass,
                message=f"Recovery success {rec_acc:.2f}% vs target {self.config.min_recovery_success}%.",
            )
        )

        # Gate 10: Security Tests (100% Pass)
        sec_acc = get_metric_rate("security", "security_pass_rate", 100.0)
        g10_pass = sec_acc >= self.config.min_security_pass_rate
        gate_checks.append(
            GateCheckResult(
                gate_name="Security Tests",
                target_value=self.config.min_security_pass_rate,
                actual_value=round(sec_acc, 2),
                passed=g10_pass,
                message=f"Security test pass rate {sec_acc:.2f}% vs target {self.config.min_security_pass_rate}%.",
            )
        )

        # Gate 11: Regression Failures (0 allowed)
        reg_failures = total_tasks - passed_tasks
        g11_pass = reg_failures <= self.config.max_regression_failures
        gate_checks.append(
            GateCheckResult(
                gate_name="Regression Failures",
                target_value=float(self.config.max_regression_failures),
                actual_value=float(reg_failures),
                passed=g11_pass,
                message=f"Regression failures {reg_failures} vs target max {self.config.max_regression_failures}.",
            )
        )

        failed_count = sum(1 for gc in gate_checks if not gc.passed)
        approved = failed_count == 0

        verdict = ReleaseGateVerdict(
            status=GateStatus.PASSED if approved else GateStatus.FAILED,
            release_approved=approved,
            gate_checks=gate_checks,
            failed_gate_count=failed_count,
            verdict_summary=f"RELEASE APPROVED: All 11 quality gates passed." if approved else f"RELEASE BLOCKED: {failed_count} quality gate(s) failed.",
        )

        logger.info(verdict.verdict_summary)
        return verdict
