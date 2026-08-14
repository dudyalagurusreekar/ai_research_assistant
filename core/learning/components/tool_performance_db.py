"""ToolPerformanceDatabase for tracking tool reliability, latency, and context efficiency."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from utils.logger import get_logger
from core.learning.models.context import ToolPerformanceMetrics

logger = get_logger("ToolPerformanceDB")


class ToolPerformanceDatabase:
    """Tracks historical performance metrics per tool capability."""

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), ".storage", "experience")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.storage_dir / "tool_performance.json"
        self._metrics: Dict[str, ToolPerformanceMetrics] = {}
        self.load()

    def load(self) -> None:
        """Loads tool metrics from disk."""
        if not self.db_file.exists():
            self._metrics = {}
            return

        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for tool_name, m_data in data.items():
                    self._metrics[tool_name] = ToolPerformanceMetrics(
                        tool_name=m_data.get("tool_name", tool_name),
                        total_calls=m_data.get("total_calls", 0),
                        successful_calls=m_data.get("successful_calls", 0),
                        failed_calls=m_data.get("failed_calls", 0),
                        total_latency_ms=m_data.get("total_latency_ms", 0.0),
                        avg_latency_ms=m_data.get("avg_latency_ms", 0.0),
                        reliability_score=m_data.get("reliability_score", 1.0),
                        context_efficiency=m_data.get("context_efficiency", 1.0),
                        last_error_type=m_data.get("last_error_type"),
                        last_updated=m_data.get("last_updated", ""),
                    )
            logger.info(f"Loaded tool performance metrics for {len(self._metrics)} tools")
        except Exception as e:
            logger.error(f"Failed to load tool performance metrics: {e}")
            self._metrics = {}

    def save(self) -> None:
        """Saves tool metrics to disk."""
        try:
            data = {
                t_name: {
                    "tool_name": m.tool_name,
                    "total_calls": m.total_calls,
                    "successful_calls": m.successful_calls,
                    "failed_calls": m.failed_calls,
                    "total_latency_ms": m.total_latency_ms,
                    "avg_latency_ms": m.avg_latency_ms,
                    "reliability_score": m.reliability_score,
                    "context_efficiency": m.context_efficiency,
                    "last_error_type": m.last_error_type,
                    "last_updated": m.last_updated,
                }
                for t_name, m in self._metrics.items()
            }
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tool performance metrics: {e}")

    def record_tool_call(
        self, tool_name: str, success: bool, latency_ms: float, error_type: Optional[str] = None
    ) -> ToolPerformanceMetrics:
        """Records an execution call for a tool and updates its health profile."""
        if tool_name not in self._metrics:
            self._metrics[tool_name] = ToolPerformanceMetrics(tool_name=tool_name)
        
        m = self._metrics[tool_name]
        m.update(success, latency_ms, error_type)
        self.save()
        return m

    def get_tool_metrics(self, tool_name: str) -> ToolPerformanceMetrics:
        """Retrieves metrics for a tool, creating a default if missing."""
        if tool_name not in self._metrics:
            self._metrics[tool_name] = ToolPerformanceMetrics(tool_name=tool_name)
        return self._metrics[tool_name]

    def rank_tools(self, tools: List[str]) -> List[str]:
        """Ranks candidate tools by reliability and speed."""
        def score(t: str):
            m = self.get_tool_metrics(t)
            # Combine reliability score with speed weighting
            latency_penalty = min(m.avg_latency_ms / 10000.0, 0.5) if m.avg_latency_ms > 0 else 0.0
            return m.reliability_score - latency_penalty

        return sorted(tools, key=score, reverse=True)

    def clear(self) -> None:
        self._metrics.clear()
        if self.db_file.exists():
            try:
                os.remove(self.db_file)
            except Exception as e:
                logger.error(f"Failed to remove tool performance db file: {e}")
