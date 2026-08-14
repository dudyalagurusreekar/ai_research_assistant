"""Smolagents Tool wrapper for the Data Intelligence Engine."""

from typing import Optional, Any
from smolagents import Tool
from core.data_intelligence.integration import get_data_engine


class DataTool(Tool):
    """Tool wrapper exposing Data Intelligence Engine capabilities to smolagents."""

    name = "data_tool"
    description = "Unified data intelligence tool for ingesting, profiling, cleaning, analyzing, visualizing, and reporting on datasets."
    inputs = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'analyze', 'profile', 'clean', 'visualize', or 'predict'",
            "nullable": True,
        },
        "dataset_name": {
            "type": "string",
            "description": "Name of the dataset",
            "nullable": True,
        },
        "source": {
            "type": "string",
            "description": "File path (CSV, JSON, SQLite) or JSON data string",
            "nullable": True,
        },
        "run_ml": {
            "type": "boolean",
            "description": "Whether to run optional machine learning workflows",
            "nullable": True,
        },
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        self._engine = get_data_engine()

    def forward(
        self,
        action: str = "analyze",
        dataset_name: str = "dataset",
        source: str = "",
        run_ml: bool = False,
    ) -> str:
        """Executes data intelligence operation."""
        try:
            if not source and hasattr(self._engine.memory, "get_dataset"):
                # Fallback check if dataset exists in memory
                mem_data = self._engine.memory.get_dataset(dataset_name)
                if mem_data:
                    source = mem_data

            if not source:
                return f"Error: No source data or file path provided for dataset '{dataset_name}'."

            report = self._engine.analyze_dataset(
                dataset_name=dataset_name,
                source=source,
                run_ml=run_ml,
                clean_data=(action == "clean" or action == "analyze"),
            )
            return report.markdown_content
        except Exception as e:
            return f"DataTool error executing '{action}' on dataset '{dataset_name}': {e}"
