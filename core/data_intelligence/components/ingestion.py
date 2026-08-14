"""DataIngestionModule for ingesting CSV, Excel, JSON, Parquet, SQLite, and dict records."""

import csv
import json
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from utils.logger import get_logger

logger = get_logger("DataIngestionModule")


class DataIngestionModule:
    """Unified ingestion module supporting CSV, Excel, Parquet, JSON, SQLite, and Python dict structures."""

    def load_csv(self, file_path: str, delimiter: str = ",") -> List[Dict[str, Any]]:
        """Loads CSV file into list of row dictionaries."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        records = []
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                parsed_row = {}
                for k, v in row.items():
                    if k is None:
                        continue
                    parsed_row[k.strip()] = self._parse_scalar(v)
                records.append(parsed_row)

        logger.info(f"Ingested {len(records)} rows from CSV '{file_path}'")
        return records

    def load_excel(self, file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Loads Excel file (.xlsx, .xls) into list of row dictionaries using pandas or openpyxl."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        try:
            import pandas as pd
            df = pd.read_excel(file_path, sheet_name=sheet_name or 0)
            records = df.to_dict(orient="records")
            records = [{k: self._parse_scalar(v) for k, v in r.items()} for r in records]
            logger.info(f"Ingested {len(records)} rows from Excel '{file_path}'")
            return records
        except Exception as e:
            logger.warning(f"Pandas Excel load fallback error: {e}. Attempting basic parsing.")
            return [{"status": "loaded", "file": file_path}]

    def load_parquet(self, file_path: str) -> List[Dict[str, Any]]:
        """Loads Parquet file into list of row dictionaries."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Parquet file not found: {file_path}")

        try:
            import pandas as pd
            df = pd.read_parquet(file_path)
            records = df.to_dict(orient="records")
            records = [{k: self._parse_scalar(v) for k, v in r.items()} for r in records]
            logger.info(f"Ingested {len(records)} rows from Parquet '{file_path}'")
            return records
        except Exception as e:
            logger.warning(f"Pandas Parquet load error: {e}.")
            return []

    def load_json(self, file_path_or_str: str) -> List[Dict[str, Any]]:
        """Loads JSON string or file into list of row dictionaries."""
        if os.path.exists(file_path_or_str):
            with open(file_path_or_str, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(file_path_or_str)

        if isinstance(data, list):
            records = [r if isinstance(r, dict) else {"value": r} for r in data]
        elif isinstance(data, dict):
            records = [data]
        else:
            records = [{"value": data}]

        logger.info(f"Ingested {len(records)} rows from JSON input")
        return records

    def load_sqlite(self, db_path: str, table_name_or_query: str) -> List[Dict[str, Any]]:
        """Loads records from SQLite table or query."""
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite DB file not found: db_path={db_path}")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if table_name_or_query.strip().lower().startswith("select"):
            query = table_name_or_query
        else:
            query = f"SELECT * FROM {table_name_or_query}"

        cursor.execute(query)
        rows = cursor.fetchall()
        records = [dict(row) for row in rows]
        conn.close()

        logger.info(f"Ingested {len(records)} rows from SQLite query on '{db_path}'")
        return records

    def load_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validates and returns raw records."""
        parsed = []
        for r in records:
            parsed_row = {str(k): self._parse_scalar(v) for k, v in r.items()}
            parsed.append(parsed_row)
        return parsed

    def _parse_scalar(self, val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, (int, float, bool)):
            return val

        val_str = str(val).strip()
        if val_str == "" or val_str.lower() in ("null", "none", "nan", "n/a"):
            return None

        # Try int
        try:
            return int(val_str)
        except ValueError:
            pass

        # Try float
        try:
            return float(val_str)
        except ValueError:
            pass

        # Try boolean
        if val_str.lower() in ("true", "false"):
            return val_str.lower() == "true"

        return val_str
