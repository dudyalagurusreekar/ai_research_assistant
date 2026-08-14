"""Load and Stress Testing Suite — Concurrency simulation, throughput evaluation, and Locust script generation."""

from __future__ import annotations

import time
import concurrent.futures
from typing import Any, Callable, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger("LoadStressTestingSuite")


class LoadStressTestingSuite:
    """Simulates high-concurrency research workloads and measures latency, RPS, error rate, and throughput."""

    def __init__(self) -> None:
        pass

    def run_concurrency_benchmark(
        self,
        task_func: Callable[[], Any],
        num_users: int = 10,
        iterations_per_user: int = 5,
    ) -> Dict[str, Any]:
        """Execute concurrent multi-threaded task execution and measure performance statistics."""
        start_time = time.perf_counter()
        total_requests = num_users * iterations_per_user
        latencies: List[float] = []
        errors = 0

        def _worker():
            nonlocal errors
            for _ in range(iterations_per_user):
                t0 = time.perf_counter()
                try:
                    task_func()
                    latencies.append((time.perf_counter() - t0) * 1000.0)
                except Exception as err:
                    errors += 1
                    logger.warning(f"Load worker error: {err}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(_worker) for _ in range(num_users)]
            concurrent.futures.wait(futures)

        total_time_sec = time.perf_counter() - start_time
        rps = round(total_requests / max(0.001, total_time_sec), 2)
        avg_lat = round(sum(latencies) / max(1, len(latencies)), 2)
        p95_lat = round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0, 2)
        error_rate = round((errors / max(1, total_requests)) * 100.0, 2)

        return {
            "num_users": num_users,
            "total_requests": total_requests,
            "total_time_sec": round(total_time_sec, 3),
            "requests_per_sec": rps,
            "avg_latency_ms": avg_lat,
            "p95_latency_ms": p95_lat,
            "error_rate_pct": error_rate,
            "successful_requests": len(latencies),
            "failed_requests": errors,
        }

    def generate_locust_script(self, target_url: str = "http://localhost:8000") -> str:
        """Generate a standalone Locust load testing Python script."""
        script_content = f'''"""Locust Load Testing Script for ARA v1.0 Core Backend Platform."""

from locust import HttpUser, task, between

class ARABackendUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def test_health_check(self):
        self.client.get("/health")

    @task(2)
    def test_research_query(self):
        self.client.post("/api/v1/research/query", json={{"query": "Transformer architecture benchmarks"}})

    @task(1)
    def test_knowledge_search(self):
        self.client.get("/api/v1/knowledge/search?q=PyTorch")
'''
        return script_content
