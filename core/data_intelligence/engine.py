"""DataIntelligenceEngine facade orchestrating all 10 modules."""

from typing import List, Dict, Any, Optional, Union
from utils.logger import get_logger
from core.data_intelligence.models.context import (
    DatasetSchema,
    DataProfile,
    StatisticalAnalysisResult,
    VisualizationConfig,
    MLModelResult,
    DataInsight,
    DataReport,
)
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

logger = get_logger("DataIntelligenceEngine")


class DataIntelligenceEngine:
    """Main facade orchestrating data ingestion, profiling, cleaning, analysis, visualization, ML, and reporting."""

    def __init__(self):
        self.ingestion = DataIngestionModule()
        self.schema_detector = SchemaDetector()
        self.profiler = DataProfiler()
        self.cleaner = DataCleaner()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.visualization_engine = VisualizationEngine()
        self.ml_engine = MLWorkflowEngine()
        self.insight_generator = InsightGenerator()
        self.report_generator = ReportGenerator()
        self.memory = DataMemory()

    def analyze_dataset(
        self,
        dataset_name: str,
        source: Union[str, List[Dict[str, Any]]],
        run_ml: bool = False,
        clean_data: bool = True,
    ) -> DataReport:
        """Runs end-to-end data analysis pipeline on dataset source."""
        # 1. Ingestion
        if isinstance(source, list):
            records = self.ingestion.load_records(source)
        elif isinstance(source, str) and self.memory.get_dataset(source) is not None:
            records = self.ingestion.load_records(self.memory.get_dataset(source))
        elif isinstance(source, str) and source.endswith(".csv"):
            records = self.ingestion.load_csv(source)
        elif isinstance(source, str) and (source.endswith(".json") or source.startswith("[")):
            records = self.ingestion.load_json(source)
        elif isinstance(source, str) and source.endswith(".db"):
            records = self.ingestion.load_sqlite(source, "data")
        else:
            raise ValueError(f"Unsupported data source type: {source}")

        # 2. Schema Detection
        schema = self.schema_detector.detect_schema(dataset_name, records)

        # 3. Data Cleaning (optional)
        if clean_data:
            records = self.cleaner.clean_dataset(records, schema=schema, drop_duplicates=True, impute_missing=True)
            schema = self.schema_detector.detect_schema(dataset_name, records)

        # 4. Data Profiling
        profile = self.profiler.profile_dataset(schema, records)

        # 5. Statistical Analysis
        stats_result = self.statistical_analyzer.analyze(schema, records)

        # 6. Visualizations
        visualizations = self.visualization_engine.auto_generate_charts(schema, records)

        # 7. Machine Learning (optional)
        ml_result = None
        if run_ml:
            numeric_cols = [c.name for c in schema.columns if c.data_type == "numeric"]
            if len(numeric_cols) >= 2:
                ml_result = self.ml_engine.run_clustering(records, numeric_cols, k=3)

        # 8. Natural Language Insights
        insights = self.insight_generator.generate_insights(profile, stats_result, ml_result)

        # 9. Report Generation
        report = self.report_generator.generate_report(
            title=f"Data Intelligence Report: {dataset_name}",
            profile=profile,
            stats_result=stats_result,
            visualizations=visualizations,
            ml_result=ml_result,
            insights=insights,
        )

        # 10. Cache in Memory
        self.memory.store_dataset(dataset_name, records, schema=schema, profile=profile)
        self.memory.store_report(dataset_name, report)

        logger.info(f"End-to-end data analysis completed for dataset '{dataset_name}'")
        return report
