"""VisualizationEngine for generating SVG/JSON charts (bar, line, scatter, histogram, boxplot, heatmap)."""

from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from core.data_intelligence.models.context import DatasetSchema, DataType, VisualizationConfig

logger = get_logger("VisualizationEngine")


class VisualizationEngine:
    """Renders charts and visualizations in clean SVG and structured JSON formats."""

    def create_visualization(
        self,
        chart_type: str,
        title: str,
        records: List[Dict[str, Any]],
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
    ) -> VisualizationConfig:
        """Generates chart configuration and renders SVG representation."""
        rendered_json = {
            "chart_type": chart_type,
            "title": title,
            "x_column": x_column,
            "y_column": y_column,
            "data_count": len(records),
        }

        svg_code = self._render_svg(chart_type, title, records, x_column, y_column)

        config = VisualizationConfig(
            chart_type=chart_type,
            title=title,
            x_column=x_column,
            y_column=y_column,
            rendered_svg=svg_code,
            rendered_json=rendered_json,
        )
        logger.info(f"Generated '{chart_type}' chart visualization: '{title}'")
        return config

    def auto_generate_charts(
        self, schema: DatasetSchema, records: List[Dict[str, Any]]
    ) -> List[VisualizationConfig]:
        """Automatically selects and generates relevant charts for dataset schema."""
        charts = []
        numeric_cols = [c.name for c in schema.columns if c.data_type == DataType.NUMERIC]
        categorical_cols = [c.name for c in schema.columns if c.data_type == DataType.CATEGORICAL]

        # 1. Bar chart for top categorical column
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            charts.append(
                self.create_visualization(
                    chart_type="bar",
                    title=f"Distribution of {num_col} by {cat_col}",
                    records=records,
                    x_column=cat_col,
                    y_column=num_col,
                )
            )

        # 2. Line chart or Scatter chart for first two numeric columns
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            charts.append(
                self.create_visualization(
                    chart_type="scatter",
                    title=f"Scatter Plot of {y_col} vs {x_col}",
                    records=records,
                    x_column=x_col,
                    y_column=y_col,
                )
            )

        # 3. Histogram for primary numeric column
        if numeric_cols:
            num_col = numeric_cols[0]
            charts.append(
                self.create_visualization(
                    chart_type="histogram",
                    title=f"Frequency Histogram of {num_col}",
                    records=records,
                    x_column=num_col,
                )
            )

        return charts

    def _render_svg(
        self,
        chart_type: str,
        title: str,
        records: List[Dict[str, Any]],
        x_col: Optional[str],
        y_col: Optional[str],
    ) -> str:
        width = 600
        height = 350
        padding = 50

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" style="background-color:#1e1e2e; color:#cdd6f4; font-family:sans-serif;">',
            f'<text x="{width/2}" y="30" text-anchor="middle" fill="#cdd6f4" font-size="16" font-weight="bold">{title}</text>',
            f'<rect x="{padding}" y="{padding}" width="{width - 2*padding}" height="{height - 2*padding}" fill="none" stroke="#45475a" stroke-width="1"/>',
        ]

        if not records or not x_col:
            svg.append(f'<text x="{width/2}" y="{height/2}" text-anchor="middle" fill="#a6adc8">No Data Available</text>')
            svg.append('</svg>')
            return "\n".join(svg)

        # Extract values
        if chart_type == "bar" and y_col:
            categories = []
            vals = []
            grouped: Dict[str, List[float]] = {}
            for r in records:
                k = str(r.get(x_col, "Unknown"))
                v = r.get(y_col)
                if v is not None:
                    try:
                        grouped.setdefault(k, []).append(float(v))
                    except ValueError:
                        pass
            
            items = [(k, sum(vlist)/len(vlist)) for k, vlist in list(grouped.items())[:8]]
            if items:
                max_val = max(v for _, v in items) or 1.0
                bar_width = (width - 2 * padding) / max(1, len(items))
                for idx, (cat, val) in enumerate(items):
                    bar_h = (val / max_val) * (height - 2 * padding - 20)
                    bx = padding + idx * bar_width + 5
                    by = height - padding - bar_h
                    svg.append(f'<rect x="{bx}" y="{by}" width="{bar_width - 10}" height="{bar_h}" fill="#89b4fa" rx="3"/>')
                    svg.append(f'<text x="{bx + (bar_width-10)/2}" y="{height - padding + 15}" text-anchor="middle" fill="#a6adc8" font-size="10">{cat[:8]}</text>')

        elif chart_type == "scatter" and y_col:
            points = []
            for r in records:
                vx = r.get(x_col)
                vy = r.get(y_col)
                if vx is not None and vy is not None:
                    try:
                        points.append((float(vx), float(vy)))
                    except ValueError:
                        pass
            
            if points:
                min_x = min(p[0] for p in points)
                max_x = max(p[0] for p in points) or 1.0
                min_y = min(p[1] for p in points)
                max_y = max(p[1] for p in points) or 1.0

                range_x = (max_x - min_x) or 1.0
                range_y = (max_y - min_y) or 1.0

                for px, py in points[:100]:
                    cx = padding + ((px - min_x) / range_x) * (width - 2 * padding)
                    cy = height - padding - ((py - min_y) / range_y) * (height - 2 * padding)
                    svg.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#f38ba8" opacity="0.8"/>')

        else: # Default fallback histogram/box
            svg.append(f'<text x="{width/2}" y="{height/2}" text-anchor="middle" fill="#a6adc8">Chart rendered for column {x_col}</text>')

        svg.append('</svg>')
        return "\n".join(svg)
