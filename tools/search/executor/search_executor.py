"""Search Executor for parallel async provider execution with timeouts, retries, and failover."""

import time
import asyncio
from typing import List
from tools.search.interfaces.provider import ISearchExecutor, ISearchProvider
from tools.search.models.search_models import (
    SearchQuery,
    SearchResultItem,
    NormalizedSearchResult,
    SearchMetrics,
)
from infrastructure.logging.logger import StructuredLogger


class SearchExecutor(ISearchExecutor):
    """Executes search queries in parallel across multiple providers with retries, timeouts, and failover."""

    def __init__(self, max_retries: int = 2) -> None:
        self._logger = StructuredLogger("SearchExecutor")
        self._max_retries = max_retries

    async def execute_search(
        self,
        query: SearchQuery,
        providers: List[ISearchProvider],
    ) -> NormalizedSearchResult:
        """Execute search tasks across providers concurrently."""
        start_time = time.time()
        metrics = SearchMetrics()
        raw_items: List[SearchResultItem] = []

        if not providers:
            self._logger.warning("No providers specified for execution.")
            metrics.total_execution_time_ms = (time.time() - start_time) * 1000
            return NormalizedSearchResult(query=query, results=[], metrics=metrics)

        async def _run_provider(provider: ISearchProvider) -> List[SearchResultItem]:
            p_name = provider.provider_name
            metrics.providers_attempted.append(p_name)
            p_start = time.time()
            
            attempts = 0
            while attempts <= self._max_retries:
                attempts += 1
                try:
                    results = await asyncio.wait_for(
                        provider.search(query),
                        timeout=query.timeout_seconds,
                    )
                    metrics.provider_latencies_ms[p_name] = (time.time() - p_start) * 1000
                    return results
                except asyncio.TimeoutError:
                    self._logger.warning(f"Timeout calling provider '{p_name}' (attempt {attempts}/{self._max_retries + 1})")
                except Exception as e:
                    self._logger.warning(f"Error calling provider '{p_name}': {e} (attempt {attempts}/{self._max_retries + 1})")
                
                if attempts <= self._max_retries:
                    await asyncio.sleep(0.05 * (2 ** (attempts - 1)))

            metrics.providers_failed.append(p_name)
            metrics.provider_latencies_ms[p_name] = (time.time() - p_start) * 1000
            return []

        tasks = [_run_provider(p) for p in providers]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results_list:
            if isinstance(res, list):
                raw_items.extend(res)
            elif isinstance(res, Exception):
                self._logger.error(f"Unhandled exception in provider execution task: {res}")

        metrics.total_raw_results = len(raw_items)
        metrics.total_execution_time_ms = (time.time() - start_time) * 1000

        self._logger.info(
            f"Executed search across {len(providers)} providers: {len(raw_items)} raw items retrieved "
            f"in {metrics.total_execution_time_ms:.2f}ms"
        )
        return NormalizedSearchResult(query=query, results=raw_items, metrics=metrics)
