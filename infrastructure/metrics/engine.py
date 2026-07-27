"""Metrics Engine calculating latency, cache hit rates, estimated LLM costs, and throughput."""

import time
from typing import Any, Dict, Optional
from infrastructure.cache.cache import MultiDomainCache
from infrastructure.monitoring.monitor import InfrastructureMonitor


class MetricsEngine:
    """Calculates operational performance metrics, cache statistics, estimated LLM cost, and throughput."""

    # Default cost per 1k tokens (e.g. Gemini / OpenAI average benchmark)
    INPUT_COST_PER_1K: float = 0.0005
    OUTPUT_COST_PER_1K: float = 0.0015

    def __init__(
        self,
        monitor: Optional[InfrastructureMonitor] = None,
        cache: Optional[MultiDomainCache] = None,
    ) -> None:
        self.monitor = monitor or InfrastructureMonitor()
        self.cache = cache or MultiDomainCache()
        self.start_time: float = time.time()

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate LLM dollar cost based on token consumption."""
        input_cost = (prompt_tokens / 1000.0) * self.INPUT_COST_PER_1K
        output_cost = (completion_tokens / 1000.0) * self.OUTPUT_COST_PER_1K
        return round(input_cost + output_cost, 6)

    def get_metrics_report(self) -> Dict[str, Any]:
        """Compile a comprehensive metrics report."""
        elapsed_seconds = max(0.001, time.time() - self.start_time)
        summary = self.monitor.get_summary()

        estimated_cost = self.calculate_cost(
            prompt_tokens=summary["prompt_tokens"],
            completion_tokens=summary["completion_tokens"],
        )

        total_requests = sum(summary["tool_calls"].values())
        throughput_qps = total_requests / elapsed_seconds

        return {
            "elapsed_seconds": round(elapsed_seconds, 2),
            "total_tokens": summary["total_tokens"],
            "prompt_tokens": summary["prompt_tokens"],
            "completion_tokens": summary["completion_tokens"],
            "estimated_llm_cost_usd": estimated_cost,
            "cache_hit_rate_pct": round(self.cache.get_hit_rate(), 2),
            "throughput_qps": round(throughput_qps, 4),
            "tool_call_breakdown": summary["tool_calls"],
            "average_tool_latencies_ms": summary["avg_tool_latencies_ms"],
        }
