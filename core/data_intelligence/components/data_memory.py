"""DataMemory for caching datasets, schemas, profiles, and analytical reports across sessions."""

from typing import Dict, List, Any, Optional
from utils.logger import get_logger
from core.data_intelligence.models.context import DatasetSchema, DataProfile, DataReport

logger = get_logger("DataMemory")


class DataMemory:
    """In-memory and persistent store for analytical data frames and reports."""

    def __init__(self):
        self._datasets: Dict[str, List[Dict[str, Any]]] = {}
        self._schemas: Dict[str, DatasetSchema] = {}
        self._profiles: Dict[str, DataProfile] = {}
        self._reports: Dict[str, DataReport] = {}

    def store_dataset(
        self,
        dataset_name: str,
        records: List[Dict[str, Any]],
        schema: Optional[DatasetSchema] = None,
        profile: Optional[DataProfile] = None,
    ) -> None:
        """Caches dataset records, schema, and profile."""
        self._datasets[dataset_name] = records
        if schema:
            self._schemas[dataset_name] = schema
        if profile:
            self._profiles[dataset_name] = profile
        logger.info(f"Stored dataset '{dataset_name}' with {len(records)} records in DataMemory")

    def get_dataset(self, dataset_name: str) -> Optional[List[Dict[str, Any]]]:
        return self._datasets.get(dataset_name)

    def get_schema(self, dataset_name: str) -> Optional[DatasetSchema]:
        return self._schemas.get(dataset_name)

    def get_profile(self, dataset_name: str) -> Optional[DataProfile]:
        return self._profiles.get(dataset_name)

    def store_report(self, report_name: str, report: DataReport) -> None:
        self._reports[report_name] = report

    def get_report(self, report_name: str) -> Optional[DataReport]:
        return self._reports.get(report_name)

    def clear(self) -> None:
        self._datasets.clear()
        self._schemas.clear()
        self._profiles.clear()
        self._reports.clear()
        logger.info("DataMemory cleared.")
