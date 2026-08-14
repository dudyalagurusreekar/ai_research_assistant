"""ReportGenerator for compiling multi-format Markdown, HTML, and structured analysis reports."""

from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from core.data_intelligence.models.context import (
    DataProfile,
    StatisticalAnalysisResult,
    VisualizationConfig,
    MLModelResult,
    DataInsight,
    DataReport,
)

logger = get_logger("ReportGenerator")


class ReportGenerator:
    """Renders comprehensive analytical reports in Markdown and HTML formats."""

    def generate_report(
        self,
        title: str,
        profile: DataProfile,
        stats_result: Optional[StatisticalAnalysisResult] = None,
        visualizations: Optional[List[VisualizationConfig]] = None,
        ml_result: Optional[MLModelResult] = None,
        insights: Optional[List[DataInsight]] = None,
    ) -> DataReport:
        """Compiles analytical artifacts into a unified DataReport object."""
        if visualizations is None:
            visualizations = []
        if insights is None:
            insights = []

        exec_summary = f"Comprehensive Data Intelligence Report for dataset '{profile.dataset_name}'. " \
                       f"Analyzed {profile.row_count} rows and {profile.column_count} columns. " \
                       f"Overall Quality Score: {profile.quality_report.overall_quality_score * 100:.1f}%."

        md_content = self._render_markdown(title, exec_summary, profile, stats_result, visualizations, ml_result, insights)
        html_content = self._render_html(title, exec_summary, profile, stats_result, visualizations, ml_result, insights)

        report = DataReport(
            title=title,
            dataset_name=profile.dataset_name,
            executive_summary=exec_summary,
            profile=profile,
            statistical_result=stats_result,
            visualizations=visualizations,
            ml_result=ml_result,
            insights=insights,
            markdown_content=md_content,
            html_content=html_content,
        )
        logger.info(f"Compiled DataReport '{title}': MD length={len(md_content)} chars")
        return report

    def _render_markdown(
        self,
        title: str,
        exec_summary: str,
        profile: DataProfile,
        stats: Optional[StatisticalAnalysisResult],
        visualizations: List[VisualizationConfig],
        ml: Optional[MLModelResult],
        insights: List[DataInsight],
    ) -> str:
        lines = [
            f"# {title}",
            "",
            "## Executive Summary",
            exec_summary,
            "",
            "## Dataset Profile & Quality Report",
            f"- **Dataset Name:** `{profile.dataset_name}`",
            f"- **Row Count:** {profile.row_count}",
            f"- **Column Count:** {profile.column_count}",
            f"- **Overall Quality Score:** {profile.quality_report.overall_quality_score * 100:.1f}%",
            f"- **Duplicate Rows:** {profile.quality_report.duplicate_rows_count}",
            f"- **Total Missing Cells:** {profile.quality_report.total_missing_cells}",
            "",
            "### Column Summary Table",
            "| Column | Type | Count | Nulls | Mean | Median | Min | Max | Outliers |",
            "|---|---|---|---|---|---|---|---|---|",
        ]

        for col_name, cp in profile.column_profiles.items():
            mean_s = f"{cp.mean:.2f}" if cp.mean is not None else "N/A"
            med_s = f"{cp.median:.2f}" if cp.median is not None else "N/A"
            min_s = f"{cp.min_val:.2f}" if cp.min_val is not None else "N/A"
            max_s = f"{cp.max_val:.2f}" if cp.max_val is not None else "N/A"
            lines.append(
                f"| {cp.column_name} | {cp.data_type.value} | {cp.count} | {cp.null_count} | {mean_s} | {med_s} | {min_s} | {max_s} | {cp.outlier_count} |"
            )

        if stats and stats.significant_findings:
            lines.extend([
                "",
                "## Statistical Analysis & Findings",
                ""
            ])
            for f in stats.significant_findings:
                lines.append(f"- {f}")

        if insights:
            lines.extend([
                "",
                "## Key Data Insights & Recommendations",
                ""
            ])
            for ins in insights:
                lines.append(f"### {ins.title}")
                lines.append(f"**Category:** `{ins.category}` | **Confidence:** {ins.confidence_score * 100:.0f}%")
                lines.append(f"- **Summary:** {ins.summary}")
                lines.append(f"- **Details:** {ins.detailed_explanation}")
                if ins.actionable_recommendation:
                    lines.append(f"- **Recommendation:** {ins.actionable_recommendation}")
                lines.append("")

        if visualizations:
            lines.extend([
                "## Interactive Visualizations",
                ""
            ])
            for vis in visualizations:
                lines.append(f"### {vis.title} (`{vis.chart_type}`)")
                if vis.rendered_svg:
                    lines.append("```xml")
                    lines.append(vis.rendered_svg)
                    lines.append("```")
                lines.append("")

        return "\n".join(lines)

    def _render_html(
        self,
        title: str,
        exec_summary: str,
        profile: DataProfile,
        stats: Optional[StatisticalAnalysisResult],
        visualizations: List[VisualizationConfig],
        ml: Optional[MLModelResult],
        insights: List[DataInsight],
    ) -> str:
        md = self._render_markdown(title, exec_summary, profile, stats, visualizations, ml, insights)
        # Convert simple markdown headers to basic HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 40px; background: #0f172a; color: #e2e8f0; }}
h1, h2, h3 {{ color: #38bdf8; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
th, td {{ border: 1px solid #334155; padding: 10px; text-align: left; }}
th {{ background-color: #1e293b; color: #38bdf8; }}
.insight-card {{ background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #38bdf8; }}
</style>
</head>
<body>
<h1>{title}</h1>
<p>{exec_summary}</p>
<h2>Dataset Profile</h2>
<p>Rows: {profile.row_count} | Columns: {profile.column_count} | Quality Score: {profile.quality_report.overall_quality_score * 100:.1f}%</p>
"""
        for vis in visualizations:
            if vis.rendered_svg:
                html += f"<div><h3>{vis.title}</h3>{vis.rendered_svg}</div>"
        html += "</body></html>"
        return html
