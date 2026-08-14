"""DataCleaner for missing value imputation, duplicate removal, outlier handling, and type coercion."""

from typing import List, Dict, Any, Optional
import copy
import statistics
from utils.logger import get_logger
from core.data_intelligence.models.context import DatasetSchema, DataType

logger = get_logger("DataCleaner")


class DataCleaner:
    """Automates dataset cleaning, missing value imputation, and outlier capping."""

    def clean_dataset(
        self,
        records: List[Dict[str, Any]],
        schema: Optional[DatasetSchema] = None,
        drop_duplicates: bool = True,
        impute_missing: bool = True,
        cap_outliers: bool = False,
    ) -> List[Dict[str, Any]]:
        """Applies data cleaning transformations on dataset records."""
        if not records:
            return []

        cleaned = copy.deepcopy(records)

        # 1. Drop duplicates
        if drop_duplicates:
            seen = set()
            deduped = []
            for r in cleaned:
                # Convert dict to hashable tuple
                tup = tuple(sorted((k, str(v)) for k, v in r.items()))
                if tup not in seen:
                    seen.add(tup)
                    deduped.append(r)
            cleaned = deduped

        # 2. Impute missing values
        if impute_missing and schema:
            for col in schema.columns:
                vals = [r.get(col.name) for r in cleaned if r.get(col.name) is not None]
                if not vals:
                    continue

                if col.data_type == DataType.NUMERIC:
                    try:
                        num_vals = [float(v) for v in vals]
                        fill_val = round(statistics.median(num_vals), 4)
                    except Exception:
                        fill_val = 0.0
                elif col.data_type in (DataType.CATEGORICAL, DataType.TEXT):
                    try:
                        mode_val = statistics.mode([str(v) for v in vals])
                        fill_val = mode_val
                    except Exception:
                        fill_val = "Unknown"
                else:
                    fill_val = None

                for r in cleaned:
                    if r.get(col.name) is None and fill_val is not None:
                        r[col.name] = fill_val

        # 3. Cap outliers (Winsorization at 1.5 * IQR)
        if cap_outliers and schema:
            for col in schema.columns:
                if col.data_type == DataType.NUMERIC:
                    nums = [float(r[col.name]) for r in cleaned if r.get(col.name) is not None]
                    if len(nums) > 4:
                        nums.sort()
                        n = len(nums)
                        q25 = nums[int(n * 0.25)]
                        q75 = nums[int(n * 0.75)]
                        iqr = q75 - q25
                        lower = q25 - (1.5 * iqr)
                        upper = q75 + (1.5 * iqr)

                        for r in cleaned:
                            if r.get(col.name) is not None:
                                try:
                                    val = float(r[col.name])
                                    if val < lower:
                                        r[col.name] = round(lower, 4)
                                    elif val > upper:
                                        r[col.name] = round(upper, 4)
                                except Exception:
                                    pass

        logger.info(f"Cleaned dataset: input rows={len(records)}, output rows={len(cleaned)}")
        return cleaned
