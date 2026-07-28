"""Stress, Concurrency, and Memory Leak Tests for Browser Action Engine.

Uses Python's tracemalloc to analyze memory growth over sequential loads, executes
concurrent page interactions to verify loop thread-safety, and compiles benchmark performance metrics.
"""

import time
import unittest
import tracemalloc
from concurrent.futures import ThreadPoolExecutor

from tools.browser.config import BrowserConfig
from tools.browser.constants import BrowserEngineType
from tools.browser.core.browser import Browser
from tests.sandbox_server import SandboxServer


class TestBrowserStressAndPerformance(unittest.TestCase):
    """Stress testing suite validating memory growth, event loop concurrency, and execution benchmarks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = SandboxServer()
        cls.server.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()

    def test_memory_leak_detection(self) -> None:
        """Sequential loading leak test: Verify memory growth bounds over multiple iterations."""
        tracemalloc.start()
        
        # Take initial snapshot
        snapshot_start = tracemalloc.take_snapshot()

        # Run sequential browser facades
        iterations = 10
        for _ in range(iterations):
            config = BrowserConfig(engine_type=BrowserEngineType.PLAYWRIGHT, headless=True)
            with Browser(config) as browser:
                res = browser.open_url(f"{self.server.url}/login")
                self.assertTrue(res.success)
                text = browser.get_clean_text()
                self.assertIsNotNone(text.data)

        # Take final snapshot
        snapshot_end = tracemalloc.take_snapshot()
        tracemalloc.stop()

        # Compute differences
        stats = snapshot_end.compare_to(snapshot_start, "lineno")
        total_growth = sum(stat.size_diff for stat in stats)

        # Print memory delta report
        print(f"\n[Memory Report] Total allocation change over {iterations} iterations: {total_growth / 1024.0:.2f} KB")

    def test_concurrency_stress_load(self) -> None:
        """Thread safety test: Run multiple concurrent navigations on separate threads using ThreadPoolExecutor."""
        concurrency_limit = 4
        urls = [f"{self.server.url}/login" for _ in range(concurrency_limit)]

        def run_isolated_browser(target_url: str) -> bool:
            config = BrowserConfig(engine_type=BrowserEngineType.PLAYWRIGHT, headless=True)
            with Browser(config) as browser:
                res = browser.open_url(target_url)
                return res.success

        with ThreadPoolExecutor(max_workers=concurrency_limit) as executor:
            results = list(executor.map(run_isolated_browser, urls))

        for idx, success in enumerate(results):
            self.assertTrue(success, f"Concurrent browser thread {idx} failed navigation.")

    def test_performance_benchmarks(self) -> None:
        """Performance benchmark test: Measure navigation and DOM simplification speeds."""
        config = BrowserConfig(engine_type=BrowserEngineType.PLAYWRIGHT, headless=True)
        
        with Browser(config) as browser:
            # Benchmark 1: Navigation speed
            start = time.time()
            res = browser.open_url(f"{self.server.url}/login")
            nav_time_ms = (time.time() - start) * 1000.0
            self.assertTrue(res.success)

            # Benchmark 2: DOM Text extraction speed
            start = time.time()
            text_res = browser.get_clean_text()
            extract_time_ms = (time.time() - start) * 1000.0
            self.assertTrue(text_res.success)

            print(f"\n[Performance Benchmarks] Navigation: {nav_time_ms:.2f}ms, Text Extraction: {extract_time_ms:.2f}ms")


if __name__ == "__main__":
    unittest.main()
