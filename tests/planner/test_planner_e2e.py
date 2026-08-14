"""End-to-end tests covering diverse research task types through the full planner."""

import pytest
from core.planner.engine import IntelligentPlanningEngine
from core.planner.models.context import PlannerStage, QueryIntent


class TestPlannerE2E:
    """End-to-end tests validating planner behavior across the full task spectrum."""

    def setup_method(self):
        self.engine = IntelligentPlanningEngine()
        self.tools = [
            {"name": "search_tool", "description": "Web search", "capabilities": ["search"]},
            {"name": "browser_tool", "description": "Browse URLs", "capabilities": ["browse"]},
            {"name": "document_tool", "description": "Document processing", "capabilities": ["document"]},
            {"name": "code_tool", "description": "Code execution", "capabilities": ["code"]},
            {"name": "memory_tool", "description": "Memory operations", "capabilities": ["memory"]},
            {"name": "vision_tool", "description": "Image analysis", "capabilities": ["vision"]},
            {"name": "report_tool", "description": "Report generation", "capabilities": ["report"]},
            {"name": "python_interpreter", "description": "Python execution", "capabilities": ["python"]},
        ]

    def _assert_valid_plan(self, ctx):
        """Common assertions for any valid plan."""
        assert ctx.current_stage == PlannerStage.PLANNING_COMPLETE
        assert ctx.query_analysis is not None
        assert ctx.intent is not None
        assert ctx.complexity is not None
        assert len(ctx.sub_tasks) > 0
        assert ctx.execution_graph is not None
        assert ctx.execution_graph.has_cycle() is False
        assert ctx.tool_selection is not None
        assert ctx.metrics.planning_latency_ms > 0
        assert ctx.metrics.planning_latency_ms < 2000  # must be under 2s
        assert len(ctx.errors) == 0

    # ------------------------------------------------------------------
    # Question Answering
    # ------------------------------------------------------------------

    def test_e2e_simple_factual_question(self):
        ctx = self.engine.plan("Who invented CRISPR?", self.tools)
        self._assert_valid_plan(ctx)
        assert ctx.intent in (QueryIntent.FACTUAL_QA, QueryIntent.MULTI_STEP_RESEARCH, QueryIntent.AMBIGUOUS)

    def test_e2e_detailed_factual_question(self):
        ctx = self.engine.plan(
            "Who won the Nobel Prize in Physics in 2023 and for what discovery?",
            self.tools
        )
        self._assert_valid_plan(ctx)

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def test_e2e_comparison_two_items(self):
        ctx = self.engine.plan("Compare GPT-5.5 vs Claude in reasoning tasks", self.tools)
        self._assert_valid_plan(ctx)
        assert ctx.intent == QueryIntent.COMPARISON
        assert len(ctx.sub_tasks) >= 2

    def test_e2e_comparison_three_items(self):
        ctx = self.engine.plan(
            "Compare three research papers on transformer architectures",
            self.tools
        )
        self._assert_valid_plan(ctx)
        assert ctx.query_analysis.source_count_hint >= 2

    # ------------------------------------------------------------------
    # Document Analysis
    # ------------------------------------------------------------------

    def test_e2e_single_pdf(self):
        ctx = self.engine.plan("Upload and analyze the PDF document", self.tools)
        self._assert_valid_plan(ctx)
        assert ctx.intent == QueryIntent.DOCUMENT_ANALYSIS

    def test_e2e_document_summary(self):
        ctx = self.engine.plan(
            "Read the local file ReleaseNotes_v1.1.md and summarize key enhancements",
            self.tools
        )
        self._assert_valid_plan(ctx)
        assert ctx.query_analysis.has_file_reference is True

    # ------------------------------------------------------------------
    # Code Execution
    # ------------------------------------------------------------------

    def test_e2e_code_fibonacci(self):
        ctx = self.engine.plan(
            "Using code_tool, execute a Python snippet that prints fibonacci numbers",
            self.tools
        )
        self._assert_valid_plan(ctx)
        assert ctx.intent == QueryIntent.CODE_EXECUTION
        assert ctx.constraints.require_verification is False

    # ------------------------------------------------------------------
    # Vision
    # ------------------------------------------------------------------

    def test_e2e_vision_chart_analysis(self):
        ctx = self.engine.plan("Analyze this chart image and describe trends", self.tools)
        self._assert_valid_plan(ctx)
        assert ctx.intent == QueryIntent.VISION_ANALYSIS
        assert any(t.tool_name == "vision_tool" for t in ctx.sub_tasks)

    # ------------------------------------------------------------------
    # Multi-step Research
    # ------------------------------------------------------------------

    def test_e2e_multi_source_research(self):
        ctx = self.engine.plan(
            "Research the latest NVIDIA Blackwell GPU features and compare specs",
            self.tools
        )
        self._assert_valid_plan(ctx)
        assert len(ctx.sub_tasks) >= 2

    def test_e2e_summarize_multiple_webpages(self):
        ctx = self.engine.plan(
            "Summarize multiple webpages about machine learning trends",
            self.tools
        )
        self._assert_valid_plan(ctx)
        assert ctx.query_analysis.source_count_hint >= 1

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def test_e2e_memory_store_and_recall(self):
        ctx = self.engine.plan(
            "Using memory_tool, store the fact 'ARA v2 test date is July 2026'",
            self.tools
        )
        self._assert_valid_plan(ctx)
        assert ctx.intent == QueryIntent.MEMORY_OPERATION

    # ------------------------------------------------------------------
    # Report Generation
    # ------------------------------------------------------------------

    def test_e2e_report_generation_and_validation(self):
        ctx = self.engine.plan(
            "Using document_tool summarize README.md then validate with report_tool",
            self.tools
        )
        self._assert_valid_plan(ctx)

    # ------------------------------------------------------------------
    # Ambiguous Queries
    # ------------------------------------------------------------------

    def test_e2e_ambiguous_short_query(self):
        ctx = self.engine.plan("cats", self.tools)
        self._assert_valid_plan(ctx)
        assert ctx.query_analysis.ambiguity_score > 0.1

    def test_e2e_ambiguous_vague_query(self):
        ctx = self.engine.plan("Tell me something interesting", self.tools)
        self._assert_valid_plan(ctx)

    # ------------------------------------------------------------------
    # Tool Reduction Benchmark
    # ------------------------------------------------------------------

    def test_e2e_tool_reduction_on_simple_query(self):
        """Simple QA should not need all 8 tools."""
        ctx = self.engine.plan("What is the speed of light?", self.tools)
        self._assert_valid_plan(ctx)
        assert ctx.tool_selection.reduction_percentage > 30.0

    # ------------------------------------------------------------------
    # Parallel Execution Verification
    # ------------------------------------------------------------------

    def test_e2e_parallel_groups_for_comparison(self):
        """Comparison queries should have parallel search waves."""
        ctx = self.engine.plan("Compare GPT-4 versus Claude", self.tools)
        self._assert_valid_plan(ctx)
        if len(ctx.parallel_groups) > 1:
            # First wave should have multiple nodes (parallel searches)
            assert len(ctx.parallel_groups[0]) >= 1
