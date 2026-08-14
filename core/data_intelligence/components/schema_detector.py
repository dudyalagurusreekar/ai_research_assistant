"""SchemaDetector for inferring data types, nullability, uniqueness, and column metadata."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from core.data_intelligence.models.context import DataType, ColumnSchema, DatasetSchema

logger = get_logger("SchemaDetector")


class SchemaDetector:
    """Detects dataset schema, column data types, and null ratios."""

    def detect_schema(self, dataset_name: str, records: List[Dict[str, Any]]) -> DatasetSchema:
        """Analyzes records list and builds a DatasetSchema."""
        if not records:
            return DatasetSchema(dataset_name=dataset_name, row_count=0, column_count=0, columns=[])

        row_count = len(records)
        all_keys = list(dict.fromkeys([k for r in records for k in r.keys()]))

        column_schemas = []
        for key in all_keys:
            vals = [r.get(key) for r in records]
            col_schema = self._detect_column_schema(key, vals, row_count)
            column_schemas.append(col_schema)

        schema = DatasetSchema(
            dataset_name=dataset_name,
            row_count=row_count,
            column_count=len(column_schemas),
            columns=column_schemas,
        )
        logger.info(f"Detected schema for '{dataset_name}': {row_count} rows, {len(column_schemas)} columns")
        return schema

    def _detect_column_schema(self, col_name: str, values: List[Any], total_rows: int) -> ColumnSchema:
        non_nulls = [v for v in values if v is not None]
        null_count = total_rows - len(non_nulls)
        null_percentage = (null_count / total_rows) * 100.0 if total_rows > 0 else 0.0

        unique_vals = set(non_nulls)
        unique_count = len(unique_vals)

        # Infer data type
        data_type = self._infer_type(non_nulls)
        samples = non_nulls[:5]

        return ColumnSchema(
            name=col_name,
            data_type=data_type,
            nullable=null_count > 0,
            null_count=null_count,
            null_percentage=round(null_percentage, 2),
            unique_count=unique_count,
            sample_values=samples,
        )

    def _infer_type(self, non_nulls: List[Any]) -> DataType:
        if not non_nulls:
            return DataType.TEXT

        # Check boolean
        if all(isinstance(v, bool) or str(v).lower() in ("true", "false") for v in non_nulls):
            return DataType.BOOLEAN

        # Check numeric
        is_num = True
        for v in non_nulls:
            if not isinstance(v, (int, float)):
                try:
                    float(str(v))
                except (ValueError, TypeError):
                    is_num = False
                    break
        if is_num:
            return DataType.NUMERIC

        # Check datetime
        is_date = True
        date_samples = 0
        for v in non_nulls[:10]:
            v_str = str(v)
            if len(v_str) >= 8 and ("-" in v_str or "/" in v_str):
                try:
                    datetime.fromisoformat(v_str.replace("Z", "+00:00"))
                    date_samples += 1
                except ValueError:
                    is_date = False
                    break
            else:
                is_date = False
                break
        if is_date and date_samples > 0:
            return DataType.DATETIME

        # Check categorical vs text (low cardinality relative to rows)
        if len(set(non_nulls)) <= max(10, len(non_nulls) * 0.2):
            return DataType.CATEGORICAL

        return DataType.TEXT
