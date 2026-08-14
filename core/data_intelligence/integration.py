"""Integration layer for ARA v2.5 Data Intelligence Engine."""

from typing import Optional, Dict, Any, List
from utils.logger import get_logger
from core.data_intelligence.engine import DataIntelligenceEngine
from core.data_intelligence.models.context import DataReport

logger = get_logger("DataIntegration")

_global_data_engine: Optional[DataIntelligenceEngine] = None


def get_data_engine() -> DataIntelligenceEngine:
    """Returns singleton instance of DataIntelligenceEngine."""
    global _global_data_engine
    if _global_data_engine is None:
        _global_data_engine = DataIntelligenceEngine()
    return _global_data_engine


def reset_data_engine() -> None:
    """Resets global data engine singleton instance."""
    global _global_data_engine
    _global_data_engine = None


class DataIntegrationAdapter:
    """Adapter facilitating integration between Data Intelligence Engine and Agent runtimes."""

    def __init__(self, engine: Optional[DataIntelligenceEngine] = None):
        self.engine = engine or get_data_engine()

    def process_data_source(
        self, dataset_name: str, source: Any, run_ml: bool = False
    ) -> DataReport:
        """Processes data source and returns compiled analytical report."""
        return self.engine.analyze_dataset(dataset_name, source, run_ml=run_ml)
