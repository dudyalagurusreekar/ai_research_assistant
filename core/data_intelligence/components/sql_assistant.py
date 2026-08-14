"""Text-to-SQL Assistant & SQL Query Execution Engine."""

import sqlite3
import re
import logging
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger("SQLAssistant")


class SQLAssistant:
    """Translates natural language questions to SQL and executes safe queries on in-memory SQLite tables."""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)

    def load_table(self, table_name: str, records: List[Dict[str, Any]]) -> str:
        """Register list of dict records as SQLite table."""
        if not records:
            return table_name

        # Sanitize table name
        clean_table = re.sub(r"\W+", "_", table_name).lower()
        cols = list(records[0].keys())
        cols_def = ", ".join([f'"{c}" TEXT' for c in cols])

        cursor = self.conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS "{clean_table}"')
        cursor.execute(f'CREATE TABLE "{clean_table}" ({cols_def})')

        for row in records:
            vals = [str(row.get(c)) if row.get(c) is not None else None for c in cols]
            placeholders = ", ".join(["?"] * len(cols))
            cursor.execute(f'INSERT INTO "{clean_table}" VALUES ({placeholders})', vals)

        self.conn.commit()
        logger.info(f"Loaded {len(records)} records into SQLite in-memory table '{clean_table}'")
        return clean_table

    def generate_sql(self, natural_query: str, table_name: str, columns: List[str]) -> str:
        """Heuristic Text-to-SQL query generator for standard aggregation queries."""
        q_lower = natural_query.lower()
        cols_str = ", ".join([f'"{c}"' for c in columns])

        if "average" in q_lower or "avg" in q_lower:
            num_col = next((c for c in columns if "rate" in c.lower() or "score" in c.lower() or "val" in c.lower()), columns[0])
            return f'SELECT AVG(CAST("{num_col}" AS FLOAT)) as avg_{num_col} FROM "{table_name}"'

        if "count" in q_lower or "how many" in q_lower:
            return f'SELECT COUNT(*) as total_count FROM "{table_name}"'

        if "top" in q_lower or "highest" in q_lower:
            sort_col = next((c for c in columns if "rate" in c.lower() or "score" in c.lower() or "val" in c.lower()), columns[0])
            return f'SELECT * FROM "{table_name}" ORDER BY CAST("{sort_col}" AS FLOAT) DESC LIMIT 5'

        return f'SELECT * FROM "{table_name}" LIMIT 20'

    def execute_sql(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Execute raw SQL statement with safety limit guards."""
        q_clean = query.strip()
        if not q_clean.lower().startswith("select"):
            raise ValueError("SQL Security Error: Only SELECT queries are permitted.")

        cursor = self.conn.cursor()
        cursor.execute(q_clean)

        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(limit)
        results = [dict(zip(cols, row)) for row in rows]

        return {
            "query": q_clean,
            "columns": cols,
            "row_count": len(results),
            "records": results,
        }
