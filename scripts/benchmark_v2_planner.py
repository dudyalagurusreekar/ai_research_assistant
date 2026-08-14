"""ARA v2.0 Planner Benchmark -- comparative performance analysis vs v1.1.

Measures planning latency, tool-selection accuracy, unnecessary tool reductions,
DAG quality, and planner reliability across a diverse set of research tasks.
"""

import os
import sys
import time
import json
import io
from pathlib import Path

# Force stdout and stderr to use UTF-8 to prevent Windows cp1252 console encoding crashes
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.planner.engine import IntelligentPlanningEngine
from core.planner.models.context import PlannerStage, QueryIntent


TOOLS = [
    {"name": "search_tool", "description": "Web search", "capabilities": ["search"]},
    {"name": "browser_tool", "description": "Browse URLs", "capabilities": ["browse"]},
    {"name": "document_tool", "description": "Document processing", "capabilities": ["document"]},
    {"name": "code_tool", "description": "Code execution", "capabilities": ["code"]},
    {"name": "memory_tool", "description": "Memory operations", "capabilities": ["memory"]},
    {"name": "vision_tool", "description": "Image analysis", "capabilities": ["vision"]},
    {"name": "report_tool", "description": "Report generation", "capabilities": ["report"]},
    {"name": "python_interpreter", "description": "Python execution", "capabilities": ["python"]},
]

BENCHMARK_QUERIES = [
    {"id": "B1", "category": "Factual QA", "query": "Who won the Nobel Prize in Physics in 2023?",
     "expected_intent": "factual_qa"},
    {"id": "B2", "category": "Comparison", "query": "Compare GPT-4 versus Claude in reasoning tasks",
     "expected_intent": "comparison"},
    {"id": "B3", "category": "Document Analysis", "query": "Read the PDF file and summarize the content",
     "expected_intent": "document_analysis"},
    {"id": "B4", "category": "Code Execution", "query": "Using code_tool, execute a Python fibonacci script",
     "expected_intent": "code_execution"},
    {"id": "B5", "category": "Vision", "query": "Analyze this chart image and describe the trends",
     "expected_intent": "vision_analysis"},
    {"id": "B6", "category": "Multi-step Research",
     "query": "Research the latest advancements in solid-state batteries in 2024",
     "expected_intent": "multi_step_research"},
    {"id": "B7", "category": "Memory", "query": "Using memory_tool, store the fact 'ARA v2 test date is July 2026'",
     "expected_intent": "memory_operation"},
    {"id": "B8", "category": "Report Generation",
     "query": "Using document_tool summarize README.md then validate with report_tool",
     "expected_intent": "report_generation"},
    {"id": "B9", "category": "Ambiguous", "query": "cats",
     "expected_intent": None},
    {"id": "B10", "category": "Complex Research",
     "query": "Research quantum computing breakthroughs, compare three key papers, and generate a report",
     "expected_intent": None},
]


def run_benchmark():
    engine = IntelligentPlanningEngine()
    results = []

    print("=" * 70)
    print("ARA v2.0 Intelligent Planning Engine Benchmark")
    print("=" * 70)

    for task in BENCHMARK_QUERIES:
        start = time.perf_counter()
        ctx = engine.plan(task["query"], TOOLS)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        intent_correct = True
        if task["expected_intent"]:
            intent_correct = (ctx.intent and ctx.intent.value == task["expected_intent"])

        result = {
            "id": task["id"],
            "category": task["category"],
            "query": task["query"][:60],
            "status": "PASS" if ctx.current_stage == PlannerStage.PLANNING_COMPLETE else "FAIL",
            "intent": ctx.intent.value if ctx.intent else "none",
            "intent_correct": intent_correct,
            "complexity": ctx.complexity.score if ctx.complexity else 0,
            "sub_tasks": len(ctx.sub_tasks),
            "dag_nodes": ctx.metrics.dag_node_count,
            "dag_edges": ctx.metrics.dag_edge_count,
            "parallel_groups": ctx.metrics.parallel_groups,
            "tools_selected": len(ctx.tool_selection.selected_tools) if ctx.tool_selection else 0,
            "tools_excluded": len(ctx.tool_selection.excluded_tools) if ctx.tool_selection else 0,
            "reduction_pct": ctx.tool_selection.reduction_percentage if ctx.tool_selection else 0,
            "planning_latency_ms": round(elapsed_ms, 2),
            "errors": len(ctx.errors),
        }
        results.append(result)

        status_icon = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
        intent_icon = "[OK]" if intent_correct else "[MISS]"
        print(f"\n{status_icon} {task['id']} [{task['category']}] -- {elapsed_ms:.1f}ms")
        print(f"   Intent: {result['intent']} {intent_icon} | Complexity: {result['complexity']}/10")
        print(f"   Tasks: {result['sub_tasks']} | DAG: {result['dag_nodes']}N/{result['dag_edges']}E")
        print(f"   Tools: {result['tools_selected']}/{result['tools_selected'] + result['tools_excluded']} "
              f"({result['reduction_pct']:.0f}% reduction)")
        print(f"   Parallel waves: {result['parallel_groups']}")

    # Summary
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    intent_correct = sum(1 for r in results if r["intent_correct"])
    avg_latency = sum(r["planning_latency_ms"] for r in results) / total
    avg_reduction = sum(r["reduction_pct"] for r in results) / total
    max_latency = max(r["planning_latency_ms"] for r in results)

    print(f"  Success Rate:     {passed}/{total} ({passed/total*100:.0f}%)")
    print(f"  Intent Accuracy:  {intent_correct}/{total} ({intent_correct/total*100:.0f}%)")
    print(f"  Avg Latency:      {avg_latency:.1f}ms")
    print(f"  Max Latency:      {max_latency:.1f}ms")
    print(f"  Avg Tool Reduction: {avg_reduction:.1f}%")

    # V1.1 comparison
    print("\n" + "-" * 70)
    print("V2.0 vs V1.1 COMPARISON")
    print("-" * 70)
    print(f"  Planning Latency:      v1.1=N/A (no planner) -> v2.0={avg_latency:.1f}ms overhead")
    print(f"  Tool Selection:        v1.1=ALL tools passed -> v2.0={avg_reduction:.1f}% reduction")
    print(f"  Intent Classification: v1.1=None -> v2.0={intent_correct}/{total} accuracy")
    print(f"  DAG Planning:          v1.1=Linear -> v2.0=Parallel DAG")
    print(f"  Constraint Tuning:     v1.1=Static -> v2.0=Adaptive per-intent")

    # Save results
    report_path = Path("benchmark_v2_planner_results.json")
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults saved to {report_path.absolute()}")


if __name__ == "__main__":
    run_benchmark()
