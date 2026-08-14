"""Tests for TaskDecomposer component."""

import pytest
from core.planner.components.query_analyzer import QueryAnalyzer
from core.planner.components.intent_classifier import IntentClassifier
from core.planner.components.task_decomposer import TaskDecomposer
from core.planner.models.context import PlannerContext, QueryIntent


class TestTaskDecomposer:
    def setup_method(self):
        self.analyzer = QueryAnalyzer()
        self.classifier = IntentClassifier()
        self.decomposer = TaskDecomposer()

    def _prepare_ctx(self, query: str) -> PlannerContext:
        ctx = PlannerContext(user_query=query)
        self.analyzer.analyze(ctx)
        self.classifier.classify(ctx)
        return ctx

    def test_component_name(self):
        assert self.decomposer.component_name == "TaskDecomposer"

    def test_factual_qa_decomposition(self):
        ctx = self._prepare_ctx("Who won the Nobel Prize in Physics in 2023?")
        tasks = self.decomposer.decompose(ctx)
        assert len(tasks) >= 1
        tool_names = [t.tool_name for t in tasks]
        assert "search_tool" in tool_names or "python_interpreter" in tool_names

    def test_comparison_decomposition(self):
        ctx = self._prepare_ctx("Compare GPT-4 versus Claude")
        tasks = self.decomposer.decompose(ctx)
        assert len(tasks) >= 2  # at least search + compare

    def test_code_execution_decomposition(self):
        ctx = self._prepare_ctx("Using code_tool, execute a Python script")
        tasks = self.decomposer.decompose(ctx)
        assert len(tasks) >= 1
        assert any(t.tool_name == "code_tool" for t in tasks)

    def test_document_analysis_decomposition(self):
        ctx = self._prepare_ctx("Read the PDF file and summarize it")
        tasks = self.decomposer.decompose(ctx)
        assert len(tasks) >= 1
        assert any(t.tool_name == "document_tool" for t in tasks)

    def test_memory_operation_decomposition(self):
        ctx = PlannerContext(user_query="Using memory_tool, store this fact")
        self.analyzer.analyze(ctx)
        ctx.intent = QueryIntent.MEMORY_OPERATION
        ctx.intent_confidence = 0.9
        tasks = self.decomposer.decompose(ctx)
        assert len(tasks) >= 1
        assert any(t.tool_name == "memory_tool" for t in tasks)

    def test_multi_step_research_decomposition(self):
        ctx = self._prepare_ctx("Research the latest advancements in quantum computing")
        tasks = self.decomposer.decompose(ctx)
        assert len(tasks) >= 2
        tool_names = {t.tool_name for t in tasks}
        assert len(tool_names) >= 1

    def test_dependencies_set_correctly(self):
        ctx = self._prepare_ctx("Who won the Nobel Prize in Physics in 2023?")
        tasks = self.decomposer.decompose(ctx)
        if len(tasks) >= 2:
            last_task = tasks[-1]
            assert len(last_task.dependencies) > 0
            assert last_task.dependencies[0] == tasks[0].task_id

    def test_context_attached(self):
        ctx = self._prepare_ctx("What is AI?")
        self.decomposer.decompose(ctx)
        assert len(ctx.sub_tasks) > 0
        assert len(ctx.reasoning_trace) > 0

    def test_task_ids_unique(self):
        ctx = self._prepare_ctx("Compare three different AI models")
        tasks = self.decomposer.decompose(ctx)
        ids = [t.task_id for t in tasks]
        assert len(ids) == len(set(ids))
