"""InsightGenerator for generating natural language data insights and executive summaries."""

from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from core.data_intelligence.models.context import (
    DataProfile,
    StatisticalAnalysisResult,
    MLModelResult,
    DataInsight,
)

logger = get_logger("InsightGenerator")


class InsightGenerator:
    """Generates structured natural language insights from data profiles and statistical results."""

    def generate_insights(
        self,
        profile: DataProfile,
        stats_result: Optional[StatisticalAnalysisResult] = None,
        ml_result: Optional[MLModelResult] = None,
    ) -> List[DataInsight]:
        """Generates key insights across data quality, statistical patterns, and machine learning."""
        insights: List[DataInsight] = []

        # 1. Quality Insight
        q_report = profile.quality_report
        insights.append(
            DataInsight(
                title=f"Dataset Overview & Quality Assessment for '{profile.dataset_name}'",
                category="quality",
                summary=f"The dataset contains {profile.row_count} rows and {profile.column_count} columns with an overall quality score of {q_report.overall_quality_score * 100:.1f}%.",
                detailed_explanation=f"Identified {q_report.total_missing_cells} missing values and {q_report.duplicate_rows_count} duplicate rows.",
                actionable_recommendation="Impute missing numerical cells with median values and drop duplicate rows before modeling." if q_report.issues else "Dataset quality is high and ready for analysis.",
                confidence_score=1.0,
            )
        )

        # 2. Statistical / Correlation Insight
        if stats_result and stats_result.significant_findings:
            top_findings = "; ".join(stats_result.significant_findings[:3])
            insights.append(
                DataInsight(
                    title="Key Statistical Correlations & Patterns",
                    category="correlation",
                    summary=f"Discovered {len(stats_result.significant_findings)} strong statistical relationships.",
                    detailed_explanation=top_findings,
                    actionable_recommendation="Leverage strongly correlated feature pairs for predictive modeling and feature selection.",
                    confidence_score=0.95,
                )
            )

        # 3. Machine Learning Insight
        if ml_result:
            if ml_result.task_type == "clustering":
                insights.append(
                    DataInsight(
                        title=f"Cluster Analysis ({ml_result.algorithm_name})",
                        category="ml",
                        summary=f"Partitioned dataset into {ml_result.metrics.get('k', 0):.0f} distinct clusters.",
                        detailed_explanation=f"Cluster distribution: {ml_result.predictions_summary}",
                        actionable_recommendation="Use cluster segmentations for targeted user profiling and decision rules.",
                        confidence_score=0.9,
                    )
                )
            elif ml_result.task_type == "regression":
                r2 = ml_result.metrics.get("r2_score", 0.0)
                insights.append(
                    DataInsight(
                        title="Linear Regression Trend Model",
                        category="ml",
                        summary=f"Fit regression model with R^2 score of {r2:.4f}.",
                        detailed_explanation=f"Formula: {ml_result.predictions_summary.get('formula', '')}",
                        actionable_recommendation="Incorporate regression trend for predictive forecasting.",
                        confidence_score=0.9,
                    )
                )

        logger.info(f"Generated {len(insights)} analytical insights for dataset '{profile.dataset_name}'")
        return insights
