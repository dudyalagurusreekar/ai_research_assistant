"""Benchmark Report Generator creating professional markdown reports from evaluation models."""

from tools.benchmark.interfaces.benchmark_interfaces import IBenchmarkReportGenerator
from tools.benchmark.models.benchmark_models import BenchmarkReportModel
from infrastructure.logging.logger import StructuredLogger


class BenchmarkReportGenerator(IBenchmarkReportGenerator):
    """Generates executive and technical markdown evaluation reports summarizing benchmark runs."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("BenchmarkReportGenerator")

    def generate_report(self, report_model: BenchmarkReportModel) -> str:
        """Generate comprehensive Markdown report text."""
        m = report_model.metrics
        lines = []

        lines.append(f"# {report_model.suite_name} - Evaluation Report")
        lines.append(f"**Report ID:** `{report_model.report_id}` | **Generated At:** {report_model.created_at}\n")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append(
            f"The benchmark evaluation run completed with **{m.accuracy_percentage}% overall accuracy** across "
            f"**{m.total_tasks} tasks** ({m.passed_tasks} passed, {m.failed_tasks} failed). "
            f"Average task latency was **{m.avg_latency_ms} ms** with an estimated cost of **${m.estimated_cost_usd}**.\n"
        )

        # Performance & Accuracy Breakdown
        lines.append("## Accuracy Breakdown by Difficulty Level")
        lines.append("| Difficulty Level | Accuracy (%) |")
        lines.append("|------------------|--------------|")
        lines.append(f"| GAIA Level 1     | {m.level_1_accuracy}% |")
        lines.append(f"| GAIA Level 2     | {m.level_2_accuracy}% |")
        lines.append(f"| GAIA Level 3     | {m.level_3_accuracy}% |")
        lines.append("")

        # Failure Taxonomy Distribution
        lines.append("## Failure Taxonomy Distribution")
        if report_model.error_breakdown:
            lines.append("| Error Category | Count | Percentage |")
            lines.append("|----------------|-------|------------|")
            tot_fails = max(1, m.failed_tasks)
            for cat, count in report_model.error_breakdown.items():
                pct = round((count / tot_fails) * 100.0, 1)
                lines.append(f"| `{cat}` | {count} | {pct}% |")
            lines.append("")
        else:
            lines.append("No failures recorded in this execution run.\n")

        # Telemetry & Resource Utilization
        lines.append("## Telemetry & Resource Consumption")
        lines.append(f"- **Throughput:** {m.throughput_tasks_per_sec} tasks/sec")
        lines.append(f"- **Total Tokens:** {m.total_tokens} (Prompt: {m.total_prompt_tokens}, Completion: {m.total_completion_tokens})")
        lines.append(f"- **Estimated Cost:** ${m.estimated_cost_usd}")
        lines.append(f"- **Subsystem Success Rates:** Browser {m.browser_success_rate}%, OCR {m.ocr_success_rate}%, Verification {m.verification_success_rate}%")
        lines.append(f"- **Memory Hit Rate:** {m.memory_hit_rate}%\n")

        # Tool Utilization
        if m.tool_usage_frequency:
            lines.append("## Tool Utilization Frequency")
            for tool, freq in m.tool_usage_frequency.items():
                lines.append(f"- `{tool}`: {freq} invocations")
            lines.append("")

        # Optimization Recommendations
        lines.append("## Optimization Recommendations")
        if report_model.detailed_recommendations:
            for rec in report_model.detailed_recommendations:
                lines.append(f"- **[{rec.priority.upper()}] {rec.category}:** {rec.recommendation} *(Reason: {rec.reason})*")
            lines.append("")
        elif report_model.optimization_recommendations:
            for rec_str in report_model.optimization_recommendations:
                lines.append(f"- {rec_str}")
            lines.append("")

        # Historical Comparison / Regression Summary
        if report_model.regression_report:
            reg = report_model.regression_report
            lines.append("## Regression & Historical Comparison")
            lines.append(f"- **Summary:** {reg.summary}")
            if reg.improvements:
                lines.append("- **Improvements:** " + "; ".join(reg.improvements))
            if reg.regressions:
                lines.append("- **Regressions:** " + "; ".join(reg.regressions))
            lines.append("")

        return "\n".join(lines)
