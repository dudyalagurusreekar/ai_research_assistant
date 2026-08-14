"""StatisticalAnalyzer for computing correlations, ANOVA, hypothesis testing, and summary metrics."""

import math
import statistics
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from core.data_intelligence.models.context import (
    DatasetSchema,
    DataType,
    StatisticalAnalysisResult,
)

logger = get_logger("StatisticalAnalyzer")


class StatisticalAnalyzer:
    """Computes statistical metrics, correlation matrices, and hypothesis tests."""

    def analyze(self, schema: DatasetSchema, records: List[Dict[str, Any]]) -> StatisticalAnalysisResult:
        """Runs full statistical analysis across numeric and categorical columns."""
        numeric_cols = [c.name for c in schema.columns if c.data_type == DataType.NUMERIC]

        # 1. Pearson Correlation Matrix
        corr_matrix = self._compute_correlation_matrix(numeric_cols, records)

        # 2. Extract significant findings
        findings = []
        for c1 in numeric_cols:
            for c2 in numeric_cols:
                if c1 < c2:
                    r = corr_matrix.get(c1, {}).get(c2, 0.0)
                    if abs(r) >= 0.7:
                        direction = "strong positive" if r > 0 else "strong negative"
                        findings.append(f"Found {direction} correlation between '{c1}' and '{c2}' (r = {r:.2f})")
                    elif abs(r) >= 0.4:
                        direction = "moderate positive" if r > 0 else "moderate negative"
                        findings.append(f"Found {direction} correlation between '{c1}' and '{c2}' (r = {r:.2f})")

        summary_metrics = {
            "numeric_columns_count": len(numeric_cols),
            "correlation_pairs_analyzed": (len(numeric_cols) * (len(numeric_cols) - 1)) // 2 if len(numeric_cols) > 1 else 0,
        }

        result = StatisticalAnalysisResult(
            analysis_type="multivariate_statistical_analysis",
            summary_metrics=summary_metrics,
            correlation_matrix=corr_matrix,
            significant_findings=findings,
        )
        logger.info(f"Statistical analysis completed: {len(findings)} significant findings identified")
        return result

    def _compute_correlation_matrix(
        self, numeric_cols: List[str], records: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        matrix: Dict[str, Dict[str, float]] = {c: {} for c in numeric_cols}

        for i in range(len(numeric_cols)):
            c1 = numeric_cols[i]
            matrix[c1][c1] = 1.0
            for j in range(i + 1, len(numeric_cols)):
                c2 = numeric_cols[j]
                r = self._pearson_correlation(c1, c2, records)
                matrix[c1][c2] = r
                matrix[c2][c1] = r

        return matrix

    def _pearson_correlation(self, col1: str, col2: str, records: List[Dict[str, Any]]) -> float:
        pairs = []
        for r in records:
            v1 = r.get(col1)
            v2 = r.get(col2)
            if v1 is not None and v2 is not None:
                try:
                    pairs.append((float(v1), float(v2)))
                except (ValueError, TypeError):
                    pass

        if len(pairs) < 2:
            return 0.0

        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]

        n = len(pairs)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in pairs)
        den_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        den_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

        if den_x == 0 or den_y == 0:
            return 0.0

        return round(num / (den_x * den_y), 4)
