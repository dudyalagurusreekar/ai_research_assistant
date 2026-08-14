"""Data models for ARA v2.5 Data Intelligence Engine."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from datetime import datetime, timezone
import uuid


class DataType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    TEXT = "text"
    UNKNOWN = "unknown"


class QualitySeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ColumnSchema:
    name: str
    data_type: DataType
    nullable: bool = True
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class DatasetSchema:
    dataset_name: str
    row_count: int
    column_count: int
    columns: List[ColumnSchema] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def get_column(self, col_name: str) -> Optional[ColumnSchema]:
        for col in self.columns:
            if col.name == col_name:
                return col
        return None


@dataclass
class QualityIssue:
    issue_type: str  # e.g., 'missing_values', 'duplicates', 'outliers', 'type_mismatch'
    description: str
    severity: QualitySeverity
    affected_columns: List[str] = field(default_factory=list)
    affected_rows_count: int = 0


@dataclass
class DataQualityReport:
    total_rows: int
    duplicate_rows_count: int
    total_missing_cells: int
    overall_quality_score: float  # 0.0 to 1.0
    issues: List[QualityIssue] = field(default_factory=list)


@dataclass
class ColumnProfile:
    column_name: str
    data_type: DataType
    count: int
    null_count: int
    mean: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = None
    q25: Optional[float] = None
    median: Optional[float] = None
    q75: Optional[float] = None
    max_val: Optional[float] = None
    iqr: Optional[float] = None
    skewness: Optional[float] = None
    outlier_count: int = 0
    top_categories: Dict[str, int] = field(default_factory=dict)


@dataclass
class DataProfile:
    dataset_name: str
    row_count: int
    column_count: int
    schema: DatasetSchema
    quality_report: DataQualityReport
    column_profiles: Dict[str, ColumnProfile] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class StatisticalAnalysisResult:
    analysis_type: str  # 'descriptive', 'correlation', 'anova', 't_test', 'chi_square'
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    p_values: Dict[str, float] = field(default_factory=dict)
    significant_findings: List[str] = field(default_factory=list)


@dataclass
class VisualizationConfig:
    chart_type: str  # 'bar', 'line', 'scatter', 'histogram', 'boxplot', 'heatmap'
    title: str
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    rendered_svg: Optional[str] = None
    rendered_json: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class MLModelResult:
    task_type: str  # 'classification', 'regression', 'clustering', 'anomaly_detection', 'forecasting'
    algorithm_name: str
    metrics: Dict[str, float] = field(default_factory=dict)  # e.g. {'accuracy': 0.92, 'rmse': 1.2}
    predictions_summary: Dict[str, Any] = field(default_factory=dict)
    feature_importances: Dict[str, float] = field(default_factory=dict)
    cluster_centers: List[List[float]] = field(default_factory=list)
    anomalies_count: int = 0


@dataclass
class DataInsight:
    insight_id: str = field(default_factory=lambda: f"ins_{uuid.uuid4().hex[:8]}")
    title: str = ""
    category: str = "general"  # 'trend', 'anomaly', 'correlation', 'quality', 'ml'
    summary: str = ""
    detailed_explanation: str = ""
    actionable_recommendation: str = ""
    confidence_score: float = 1.0


@dataclass
class DataReport:
    title: str
    dataset_name: str
    executive_summary: str
    profile: DataProfile
    statistical_result: Optional[StatisticalAnalysisResult] = None
    visualizations: List[VisualizationConfig] = field(default_factory=list)
    ml_result: Optional[MLModelResult] = None
    insights: List[DataInsight] = field(default_factory=list)
    markdown_content: str = ""
    html_content: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
