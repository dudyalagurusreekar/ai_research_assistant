"""End-to-end execution benchmark tests for Sprint 2 Adaptive Execution Subsystem."""

import pytest
from core.execution.integration import ExecutionIntegration
from core.execution.models.result import ExecutionStatus
from core.planner.engine import IntelligentPlanningEngine


class TestExecutionE2E:
    def setup_method(self):
        self.integration = ExecutionIntegration()
        self.planner = IntelligentPlanningEngine()
        self.executors = {
            "search_tool": lambda action, params: f"Search output for {params.get('query', '')}",
            "browser_tool": lambda action, params: f"Browsed webpage for {params.get('query', '')}",
            "document_tool": lambda action, params: "Ingested document text: ARA v2.0 release",
            "code_tool": lambda action, params: "[0, 1, 1, 2, 3]",
            "vision_tool": lambda action, params: "Chart description: upward trend",
            "memory_tool": lambda action, params: "Memory stored: ARA v2.0",
            "report_tool": lambda action, params: "Report valid: true",
            "python_interpreter": lambda action, params: "Synthesized final answer",
        }

    def test_e2e_research_workflow(self):
        ctx = self.planner.plan("Research latest solid-state battery advancements in 2024")
        plan = self.integration.optimize_execution(ctx)

        results = []
        for wave in plan.execution_waves:
            for node in wave:
                res = self.integration.execute_task(
                    task_id=node.node_id,
                    tool_name=node.tool_name,
                    action=node.action,
                    parameters=node.parameters,
                    executors=self.executors,
                )
                results.append(res)

        assert len(results) == plan.total_nodes
        assert all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.CACHED) for r in results)

    def test_e2e_caching_deduplication_on_repeated_tasks(self):
        query = "Who won the Nobel Prize in Physics in 2023?"
        ctx = self.planner.plan(query)
        plan = self.integration.optimize_execution(ctx)

        # First run — all misses
        res1 = [
            self.integration.execute_task(
                node.node_id, node.tool_name, node.action, node.parameters, self.executors
            )
            for wave in plan.execution_waves for node in wave
        ]
        assert any(r.is_cached is False for r in res1)

        # Second run — identical tasks should hit cache!
        res2 = [
            self.integration.execute_task(
                node.node_id, node.tool_name, node.action, node.parameters, self.executors
            )
            for wave in plan.execution_waves for node in wave
        ]
        assert all(r.is_cached is True for r in res2)
        assert self.integration.cache.hits >= len(res2)

    def test_e2e_graceful_degradation_on_primary_failure(self):
        failing_executors = dict(self.executors)
        failing_executors["search_tool"] = lambda a, p: (_ for _ in ()).throw(RuntimeError("Search API 503"))

        ctx = self.planner.plan("Search web for quantum computing breakthroughs")
        plan = self.integration.optimize_execution(ctx)

        results = []
        for wave in plan.execution_waves:
            for node in wave:
                res = self.integration.execute_task(
                    node.node_id, node.tool_name, node.action, node.parameters, failing_executors
                )
                results.append(res)

        # search_tool should failover gracefully to browser_tool
        degraded = [r for r in results if r.status == ExecutionStatus.DEGRADED]
        assert len(degraded) >= 1
        assert degraded[0].fallback_used == "browser_tool"
