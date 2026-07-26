"""Reporting Engine Implementation.

Aggregates events timeline, records artifact indices, fetches budget snapshots,
and compiles JSON, Markdown, and HTML reports.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from tools.browser.budget.manager import BudgetManager
from tools.browser.reporting.base import (
    ExecutionEvent,
    ReportData,
    ReportFormat,
    ReportMetadata,
    ReportingError,
)

logger = logging.getLogger("ReportingEngine.Coordinator")


class ReportingEngine:
    """Enterprise-grade Reporting Engine capturing and exporting execution sessions."""

    def __init__(self) -> None:
        """Initialize the Reporting Engine."""
        self.timeline: List[ExecutionEvent] = []
        self.artifacts: Dict[str, Any] = {}
        self.recovery_statistics: Dict[str, Any] = {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "strategies_triggered": {},
        }
        self.details: Dict[str, Any] = {}
        self._logger = logger

    def log_event(
        self,
        step_number: int,
        category: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an execution event in the timeline log.

        Args:
            step_number: Reasoning step index when event occurred.
            category: Event category (e.g. PLANNING, ACTION, RECOVERY, LOOP).
            message: Description of event.
            metadata: Custom attributes details.
        """
        event = ExecutionEvent(
            timestamp=time.time(),
            step_number=step_number,
            category=category.upper(),
            message=message,
            metadata=metadata or {},
        )
        self.timeline.append(event)
        
        # Accumulate recovery stats if category matches RECOVERY
        if category.upper() == "RECOVERY" and metadata:
            self.recovery_statistics["attempts"] += 1
            strategy = metadata.get("strategy", "unknown")
            outcome = metadata.get("success", False)
            
            strat_counts = self.recovery_statistics["strategies_triggered"]
            strat_counts[strategy] = strat_counts.get(strategy, 0) + 1
            
            if outcome:
                self.recovery_statistics["successes"] += 1
            else:
                self.recovery_statistics["failures"] += 1

    def record_artifact(self, name: str, value: Any, details: Optional[Dict[str, Any]] = None) -> None:
        """Index a downloaded file reference or extracted variable details.

        Args:
            name: Label key for artifact.
            value: Absolute path or resolved data.
            details: Custom metadata.
        """
        self.artifacts[name] = {
            "value": value,
            "timestamp": time.time(),
            "details": details or {},
        }

    def generate_report(
        self,
        metadata: ReportMetadata,
        budget_manager: Optional[BudgetManager] = None,
    ) -> ReportData:
        """Gather all metrics, timelines, and budgets to build ReportData.

        Args:
            metadata: Session metadata summary.
            budget_manager: Reference to active BudgetManager limits.

        Returns:
            ReportData: Consolidated statistics report.
        """
        # Formulate budget utilization stats if manager is available
        budget_utilization = {}
        if budget_manager:
            for cat, limit in budget_manager.limits.items():
                budget_utilization[cat.value] = {
                    "limit": limit.limit,
                    "consumed": limit.consumed,
                    "reserved": limit.reserved,
                    "usage_ratio": limit.usage_ratio,
                    "status": limit.get_status().value,
                }

        return ReportData(
            metadata=metadata,
            timeline=list(self.timeline),
            artifacts=dict(self.artifacts),
            recovery_statistics=dict(self.recovery_statistics),
            budget_utilization=budget_utilization,
            details=dict(self.details),
        )

    def export_report(self, report_data: ReportData, format_type: ReportFormat) -> str:
        """Export the consolidated report in the requested format.

        Args:
            report_data: Consolidated statistics report.
            format_type: Requested output format.

        Returns:
            str: Serialized report representation.
        """
        if format_type == ReportFormat.JSON:
            return self._export_json(report_data)
        elif format_type == ReportFormat.MARKDOWN:
            return self._export_markdown(report_data)
        elif format_type == ReportFormat.HTML:
            return self._export_html(report_data)
        else:
            raise ReportingError(f"Unsupported report export format: {format_type}")

    def _export_json(self, report_data: ReportData) -> str:
        """Compile report data into structured JSON."""
        # Convert timeline objects and metadata into simple dict representation
        timeline_list = []
        for e in report_data.timeline:
            timeline_list.append({
                "timestamp": e.timestamp,
                "step_number": e.step_number,
                "category": e.category,
                "message": e.message,
                "metadata": e.metadata,
            })

        data_dict = {
            "metadata": {
                "objective": report_data.metadata.objective,
                "status": report_data.metadata.status,
                "duration_seconds": report_data.metadata.duration_seconds,
                "start_time": report_data.metadata.start_time,
                "end_time": report_data.metadata.end_time,
                "confidence": report_data.metadata.confidence,
            },
            "timeline": timeline_list,
            "artifacts": report_data.artifacts,
            "recovery_statistics": report_data.recovery_statistics,
            "budget_utilization": report_data.budget_utilization,
            "details": report_data.details,
        }
        return json.dumps(data_dict, indent=2)

    def _export_markdown(self, report_data: ReportData) -> str:
        """Compile report data into a formatted Markdown document."""
        meta = report_data.metadata
        md = []

        md.append(f"# Browser Execution Report — {meta.status}")
        md.append("")
        md.append(f"**Objective**: {meta.objective}")
        md.append(f"- **Final Status**: {meta.status}")
        md.append(f"- **Total Duration**: {meta.duration_seconds:.2f} seconds")
        md.append(f"- **Confidence Rating**: {meta.confidence:.1%}")
        md.append("")

        # 1. Budget summary table
        if report_data.budget_utilization:
            md.append("## Resource Budget Utilization")
            md.append("")
            md.append("| Resource | Limit | Consumed | Usage Ratio | Status |")
            md.append("| --- | --- | --- | --- | --- |")
            for cat, b in report_data.budget_utilization.items():
                md.append(
                    f"| {cat} | {b['limit']:.1f} | {b['consumed']:.1f} | "
                    f"{b['usage_ratio']:.1%} | {b['status']} |"
                )
            md.append("")

        # 2. Artifacts collected list
        if report_data.artifacts:
            md.append("## Collected Artifacts")
            md.append("")
            for name, a in report_data.artifacts.items():
                md.append(f"- **{name}**: `{a['value']}` (indexed at {time.strftime('%H:%M:%S', time.localtime(a['timestamp']))})")
            md.append("")

        # 3. Recovery healing statistics
        rec = report_data.recovery_statistics
        if rec.get("attempts", 0) > 0:
            md.append("## Self-Healing Recovery Summary")
            md.append(f"- **Total Recovery Actions**: {rec['attempts']}")
            md.append(f"- **Successes**: {rec['successes']}")
            md.append(f"- **Failures**: {rec['failures']}")
            md.append("")
            md.append("### Recovery Strategy Frequencies")
            for strat, count in rec.get("strategies_triggered", {}).items():
                md.append(f"- Strategy `{strat}` triggered {count} times.")
            md.append("")

        # 4. Timeline list
        md.append("## Execution Timeline Events")
        md.append("")
        for e in report_data.timeline:
            t_str = time.strftime("%H:%M:%S", time.localtime(e.timestamp))
            md.append(f"1. **[{t_str}] Step {e.step_number}** — `[{e.category}]`: {e.message}")

        return "\n".join(md)

    def _export_html(self, report_data: ReportData) -> str:
        """Compile report data into a styled HTML page."""
        meta = report_data.metadata
        
        # Build Budget Rows
        budget_rows = ""
        if report_data.budget_utilization:
            for cat, b in report_data.budget_utilization.items():
                ratio = b["usage_ratio"] * 100
                budget_rows += f"""
                <tr>
                    <td><strong>{cat}</strong></td>
                    <td>{b['limit']:.1f}</td>
                    <td>{b['consumed']:.1f}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {min(100.0, ratio)}%"></div>
                        </div>
                        {b['usage_ratio']:.1%}
                    </td>
                    <td><span class="status-badge status-{b['status'].lower()}">{b['status']}</span></td>
                </tr>
                """

        # Build Artifact Lists
        artifact_list = ""
        if report_data.artifacts:
            for name, a in report_data.artifacts.items():
                artifact_list += f"<li><strong>{name}</strong>: <code>{a['value']}</code></li>"
        else:
            artifact_list = "<li>No artifacts collected.</li>"

        # Build Timeline Items
        timeline_items = ""
        for e in report_data.timeline:
            t_str = time.strftime("%H:%M:%S", time.localtime(e.timestamp))
            timeline_items += f"""
            <div class="timeline-item">
                <div class="timeline-time">{t_str} (Step {e.step_number})</div>
                <div class="timeline-badge badge-{e.category.lower()}">{e.category}</div>
                <div class="timeline-desc">{e.message}</div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Browser Session Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #334155;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            padding: 32px;
        }}
        h1, h2, h3 {{
            color: #1e293b;
        }}
        h1 {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 12px;
            margin-top: 0;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .meta-card {{
            background: #f1f5f9;
            padding: 16px;
            border-radius: 8px;
        }}
        .meta-label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #64748b;
            font-weight: bold;
        }}
        .meta-value {{
            font-size: 18px;
            color: #0f172a;
            margin-top: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #f8fafc;
            color: #475569;
        }}
        .progress-bar {{
            background: #e2e8f0;
            border-radius: 4px;
            height: 8px;
            width: 100px;
            display: inline-block;
            margin-right: 8px;
        }}
        .progress-fill {{
            background: #6366f1;
            height: 100%;
            border-radius: 4px;
        }}
        .status-badge {{
            padding: 4px 8px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status-healthy {{ background: #dcfce7; color: #15803d; }}
        .status-warning {{ background: #fef9c3; color: #a16207; }}
        .status-critical {{ background: #fee2e2; color: #b91c1c; }}
        .status-exhausted {{ background: #fee2e2; color: #b91c1c; }}
        .timeline {{
            margin-top: 24px;
            position: relative;
            padding-left: 24px;
            border-left: 2px solid #e2e8f0;
        }}
        .timeline-item {{
            margin-bottom: 16px;
            position: relative;
        }}
        .timeline-time {{
            font-size: 12px;
            color: #64748b;
        }}
        .timeline-badge {{
            display: inline-block;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
            margin: 4px 0;
        }}
        .badge-planning {{ background: #dbeafe; color: #1e40af; }}
        .badge-action {{ background: #dcfce7; color: #15803d; }}
        .badge-recovery {{ background: #fee2e2; color: #b91c1c; }}
        .badge-loop {{ background: #fef9c3; color: #a16207; }}
        .badge-completion {{ background: #f3e8ff; color: #6b21a8; }}
        .timeline-desc {{
            color: #334155;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Execution Session Report</h1>
        
        <div class="meta-grid">
            <div class="meta-card" style="grid-column: span 2;">
                <div class="meta-label">Target Objective</div>
                <div class="meta-value">{meta.objective}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Session Status</div>
                <div class="meta-value">{meta.status}</div>
            </div>
            <div class="meta-card">
                <div class="meta-label">Confidence Success Rating</div>
                <div class="meta-value">{meta.confidence:.1%}</div>
            </div>
        </div>

        <h2>Resource Budgets Status</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Limit</th>
                    <th>Consumed</th>
                    <th>Usage Ratio</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {budget_rows}
            </tbody>
        </table>

        <h2>Artifacts Index</h2>
        <ul>
            {artifact_list}
        </ul>

        <h2>Execution Timeline</h2>
        <div class="timeline">
            {timeline_items}
        </div>
    </div>
</body>
</html>
"""
        return html
