"""Components module for ARA v2.5 Data Intelligence Engine."""

from core.data_intelligence.components.ingestion import DataIngestionModule
from core.data_intelligence.components.schema_detector import SchemaDetector
from core.data_intelligence.components.profiler import DataProfiler
from core.data_intelligence.components.cleaner import DataCleaner
from core.data_intelligence.components.statistical_analyzer import StatisticalAnalyzer
from core.data_intelligence.components.visualization import VisualizationEngine
from core.data_intelligence.components.ml_workflow import MLWorkflowEngine
from core.data_intelligence.components.insight_generator import InsightGenerator
from core.data_intelligence.components.report_generator import ReportGenerator
from core.data_intelligence.components.data_memory import DataMemory

__all__ = [
    "DataIngestionModule",
    "SchemaDetector",
    "DataProfiler",
    "DataCleaner",
    "StatisticalAnalyzer",
    "VisualizationEngine",
    "MLWorkflowEngine",
    "InsightGenerator",
    "ReportGenerator",
    "DataMemory",
]
