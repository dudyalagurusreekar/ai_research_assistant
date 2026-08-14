"""DataProfiler for calculating column metrics, quality reports, duplicates, and outliers."""

import math
import statistics
from typing import List, Dict, Any, Optional
from collections import Counter
from utils.logger import get_logger
from core.data_intelligence.models.context import (
    DataType,
    QualitySeverity,
    DatasetSchema,
    QualityIssue,
    DataQualityReport,
    ColumnProfile,
    DataProfile,
)

logger = get_logger("DataProfiler")


class DataProfiler:
    """Profiles tabular datasets to generate statistics, quality metrics, and outlier counts."""

    def profile_dataset(self, schema: DatasetSchema, records: List[Dict[str, Any]]) -> DataProfile:
        """Profiles the dataset records based on detected schema."""
        row_count = len(records)
        col_count = len(schema.columns)

        col_profiles: Dict[str, ColumnProfile] = {}
        total_missing = 0

        for col in schema.columns:
            vals = [r.get(col.name) for r in records]
            non_nulls = [v for v in vals if v is not None]
            total_missing += (row_count - len(non_nulls))

            profile = self._profile_column(col.name, col.data_type, non_nulls, row_count)
            col_profiles[col.name] = profile

        # Quality Report & Duplicates
        quality_report = self._assess_quality(schema, records, col_profiles, total_missing)

        profile = DataProfile(
            dataset_name=schema.dataset_name,
            row_count=row_count,
            column_count=col_count,
            schema=schema,
            quality_report=quality_report,
            column_profiles=col_profiles,
        )
        logger.info(f"Profiled dataset '{schema.dataset_name}': Quality Score={quality_report.overall_quality_score:.2f}")
        return profile

    def _profile_column(self, col_name: str, data_type: DataType, non_nulls: List[Any], total_rows: int) -> ColumnProfile:
        null_count = total_rows - len(non_nulls)
        cp = ColumnProfile(
            column_name=col_name,
            data_type=data_type,
            count=len(non_nulls),
            null_count=null_count,
        )

        if data_type == DataType.NUMERIC and non_nulls:
            nums = []
            for v in non_nulls:
                try:
                    nums.append(float(v))
                except (ValueError, TypeError):
                    pass
            
            if nums:
                nums.sort()
                n = len(nums)
                cp.mean = round(sum(nums) / n, 4)
                cp.min_val = round(nums[0], 4)
                cp.max_val = round(nums[-1], 4)
                cp.median = round(statistics.median(nums), 4)

                if n > 1:
                    cp.std = round(statistics.stdev(nums), 4)

                # Quantiles & IQR
                q25_idx = int(n * 0.25)
                q75_idx = int(n * 0.75)
                cp.q25 = round(nums[q25_idx], 4)
                cp.q75 = round(nums[q75_idx], 4)
                cp.iqr = round(cp.q75 - cp.q25, 4)

                # Outliers using IQR
                lower_bound = cp.q25 - (1.5 * cp.iqr)
                upper_bound = cp.q75 + (1.5 * cp.iqr)
                outliers = [v for v in nums if v < lower_bound or v > upper_bound]
                cp.outlier_count = len(outliers)

                # Skewness approximation
                if cp.std and cp.std > 0:
                    cp.skewness = round(3.0 * (cp.mean - cp.median) / cp.std, 4)

        elif data_type in (DataType.CATEGORICAL, DataType.TEXT, DataType.BOOLEAN) and non_nulls:
            str_vals = [str(v) for v in non_nulls]
            counter = Counter(str_vals)
            cp.top_categories = dict(counter.most_common(5))

        return cp

    def _assess_quality(
        self,
        schema: DatasetSchema,
        records: List[Dict[str, Any]],
        col_profiles: Dict[str, ColumnProfile],
        total_missing: int,
    ) -> DataQualityReport:
        row_count = len(records)
        col_count = len(schema.columns)
        total_cells = row_count * col_count if row_count and col_count else 1

        # Check duplicates
        record_tuples = []
        for r in records:
            try:
                record_tuples.append(tuple(sorted((k, str(v)) for k, v in r.items())))
            except Exception:
                pass
        
        dup_count = len(record_tuples) - len(set(record_tuples))
        issues: List[QualityIssue] = []

        # Missing values issue
        missing_ratio = total_missing / total_cells
        if missing_ratio > 0.05:
            severity = QualitySeverity.CRITICAL if missing_ratio > 0.3 else QualitySeverity.WARNING
            affected_cols = [c.name for c in schema.columns if c.null_count > 0]
            issues.append(
                QualityIssue(
                    issue_type="missing_values",
                    description=f"{missing_ratio * 100:.1f}% missing cells across dataset",
                    severity=severity,
                    affected_columns=affected_cols,
                    affected_rows_count=total_missing,
                )
            )

        # Duplicate rows issue
        if dup_count > 0:
            issues.append(
                QualityIssue(
                    issue_type="duplicates",
                    description=f"Found {dup_count} duplicate rows in dataset",
                    severity=QualitySeverity.WARNING,
                    affected_rows_count=dup_count,
                )
            )

        # Outliers issue
        outlier_cols = [c for c, p in col_profiles.items() if p.outlier_count > 0]
        if outlier_cols:
            total_outliers = sum(col_profiles[c].outlier_count for c in outlier_cols)
            issues.append(
                QualityIssue(
                    issue_type="outliers",
                    description=f"Identified {total_outliers} numerical outliers across {len(outlier_cols)} columns",
                    severity=QualitySeverity.INFO,
                    affected_columns=outlier_cols,
                    affected_rows_count=total_outliers,
                )
            )

        # Overall quality score computation (1.0 = perfect)
        quality_score = max(0.0, 1.0 - (missing_ratio * 0.5) - ((dup_count / max(1, row_count)) * 0.3))

        return DataQualityReport(
            total_rows=row_count,
            duplicate_rows_count=dup_count,
            total_missing_cells=total_missing,
            overall_quality_score=round(quality_score, 4),
            issues=issues,
        )
