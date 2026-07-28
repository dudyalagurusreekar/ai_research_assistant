"""Benchmark Registry for managing supported benchmark suites and metadata."""

from typing import Dict, List, Optional
from tools.benchmark.interfaces.benchmark_interfaces import IBenchmarkRegistry
from tools.benchmark.models.benchmark_models import BenchmarkSuiteMetadata
from infrastructure.logging.logger import StructuredLogger


class BenchmarkRegistry(IBenchmarkRegistry):
    """Registry maintaining metadata for benchmark suites (GAIA, SWE-Bench, BrowseComp, WebArena, HLE, Custom)."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("BenchmarkRegistry")
        self._suites: Dict[str, BenchmarkSuiteMetadata] = {}

        # Register default initial suites
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register built-in benchmark suites."""
        gaia = BenchmarkSuiteMetadata(
            suite_id="gaia",
            name="General AI Assistants Benchmark (GAIA)",
            description="Hugging Face GAIA benchmark evaluating multi-modal, general AI assistant capabilities across 3 difficulty levels.",
            version="1.0.0",
            categories=["web_research", "file_analysis", "code_execution", "multimodal_vision", "data_integration", "multi_step_reasoning"],
            difficulty_levels=["level_1", "level_2", "level_3"],
            default_config={"concurrency": 1, "timeout_seconds": 300},
        )
        swe_bench = BenchmarkSuiteMetadata(
            suite_id="swe_bench",
            name="Software Engineering Benchmark (SWE-Bench)",
            description="Benchmark for evaluating AI models on resolving real-world GitHub issues.",
            version="1.0.0",
            categories=["code_execution", "file_analysis"],
            difficulty_levels=["medium", "hard"],
            default_config={"concurrency": 2, "timeout_seconds": 600},
        )
        browse_comp = BenchmarkSuiteMetadata(
            suite_id="browse_comp",
            name="Web Browsing Competency (BrowseComp)",
            description="Benchmark for complex web browsing, navigation, and web data extraction.",
            version="1.0.0",
            categories=["web_research", "browser"],
            difficulty_levels=["level_1", "level_2"],
            default_config={"concurrency": 1, "timeout_seconds": 240},
        )
        web_arena = BenchmarkSuiteMetadata(
            suite_id="web_arena",
            name="WebArena Environment Benchmark",
            description="Realistic web environment benchmark measuring end-to-end task completion.",
            version="1.0.0",
            categories=["web_research", "browser", "data_integration"],
            difficulty_levels=["standard"],
            default_config={"concurrency": 1, "timeout_seconds": 360},
        )
        hle = BenchmarkSuiteMetadata(
            suite_id="hle",
            name="Humanity's Last Exam (HLE)",
            description="Multi-disciplinary expert level reasoning and domain knowledge benchmark.",
            version="1.0.0",
            categories=["multi_step_reasoning", "file_analysis"],
            difficulty_levels=["expert"],
            default_config={"concurrency": 1, "timeout_seconds": 450},
        )

        for suite in [gaia, swe_bench, browse_comp, web_arena, hle]:
            self._suites[suite.suite_id] = suite

    def register_suite(self, metadata: BenchmarkSuiteMetadata) -> None:
        """Register or update a benchmark suite."""
        self._suites[metadata.suite_id] = metadata
        self._logger.info(f"Registered benchmark suite '{metadata.name}' ({metadata.suite_id})")

    def get_suite(self, suite_id: str) -> Optional[BenchmarkSuiteMetadata]:
        """Retrieve benchmark suite metadata by ID."""
        return self._suites.get(suite_id.lower())

    def list_suites(self) -> List[BenchmarkSuiteMetadata]:
        """Return list of all registered benchmark suites."""
        return list(self._suites.values())

    def unregister_suite(self, suite_id: str) -> bool:
        """Unregister a benchmark suite."""
        sid = suite_id.lower()
        if sid in self._suites:
            del self._suites[sid]
            self._logger.info(f"Unregistered benchmark suite '{sid}'")
            return True
        return False
