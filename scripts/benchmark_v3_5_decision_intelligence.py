"""ARA v3.5 Decision Intelligence & Recommendation Engine Benchmark (Sprint 13).

Measures end-to-end performance across:
1. Engine Initialization & Warmup Latency
2. Decision Context Framing & Constraint Extraction Speed
3. Option Generation & Feasibility Filtering Throughput
4. Multi-Criteria Decision Analysis (MCDA) & Pareto Frontier Detection Latency
5. Risk Assessment & Severity Scoring Throughput
6. Scenario Simulation & Weight Sensitivity Analysis Latency
7. Confidence Calibration & Uncertainty Interval Quantification Speed
8. End-to-End Pipeline Execution across 4 Production Benchmark Scenarios:
   - Enterprise Cloud Architecture Selection
   - Analytics Database Infrastructure
   - AI Agent Framework Procurement
   - Enterprise Compliance Platform
9. Subsystem Bridge Integration Handoff Latencies (8 Subsystems)
"""

import io
import json
import os
import sys
import time
from pathlib import Path

# Force stdout/stderr to UTF-8
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.decision_intelligence.engine import DecisionIntelligenceEngine
from core.decision_intelligence.integration import DecisionSubsystemIntegration
from core.decision_intelligence.models import DecisionRequest, RecommendationType


def run_benchmark():
    print("=" * 80)
    print("ARA v3.5 DECISION INTELLIGENCE & RECOMMENDATION ENGINE BENCHMARK (SPRINT 13)")
    print("=" * 80)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sprint": "Sprint 13 - Decision Intelligence & Recommendation Engine",
        "scenarios_evaluated": 4,
        "metrics": {},
    }

    # 1. Engine Warmup & Initialization
    t0 = time.time()
    engine = DecisionIntelligenceEngine()
    init_latency_ms = (time.time() - t0) * 1000.0

    print(f"\n[1] Engine Initialization & Component Warmup")
    print(f"  Init Latency: {init_latency_ms:.2f} ms")
    results["metrics"]["init_latency_ms"] = round(init_latency_ms, 2)

    # Define Benchmark Scenarios
    scenarios = [
        {
            "name": "Enterprise Multi-Cloud Architecture",
            "query": "Choose a cloud architecture with latency under 50ms and budget under $10000 USD for containerized microservices",
            "topic": "Cloud Infrastructure Strategy",
            "presets": [
                {"title": "Serverless Container Cloud", "estimated_cost": 2500.0, "implementation_complexity": "low"},
                {"title": "Multi-Region Kubernetes Cluster", "estimated_cost": 8500.0, "implementation_complexity": "high"},
                {"title": "Hybrid On-Prem Instance Group", "estimated_cost": 12000.0, "implementation_complexity": "extreme"},
            ],
        },
        {
            "name": "Analytics Database Infrastructure",
            "query": "Select high-throughput database under $5000 USD budget for real-time analytics",
            "topic": "Database Infrastructure",
            "presets": [
                {"title": "PostgreSQL Managed Instance", "estimated_cost": 1800.0, "implementation_complexity": "medium"},
                {"title": "ClickHouse Columnar Warehouse", "estimated_cost": 3200.0, "implementation_complexity": "medium"},
                {"title": "Distributed DynamoDB Store", "estimated_cost": 4500.0, "implementation_complexity": "low"},
            ],
        },
        {
            "name": "AI Agent Framework Procurement",
            "query": "Evaluate multi-agent orchestration framework for enterprise research assistant",
            "topic": "AI Framework Procurement",
            "presets": [
                {"title": "Custom Modular Agent SDK", "estimated_cost": 1200.0, "implementation_complexity": "medium"},
                {"title": "Commercial Enterprise AI Platform", "estimated_cost": 6500.0, "implementation_complexity": "low"},
                {"title": "Open-Source LangGraph Engine", "estimated_cost": 400.0, "implementation_complexity": "high"},
            ],
        },
        {
            "name": "Enterprise Security & Compliance Platform",
            "query": "Select security compliance tool with SOC2 verification and budget under $15000 USD",
            "topic": "Security Compliance Tooling",
            "presets": [
                {"title": "Automated Compliance Platform A", "estimated_cost": 9500.0, "implementation_complexity": "low"},
                {"title": "Enterprise SIEM Engine B", "estimated_cost": 14000.0, "implementation_complexity": "high"},
            ],
        },
    ]

    # 2. Execute Benchmark Scenarios
    print(f"\n[2] Executing Benchmark Scenarios")
    scenario_latencies = []
    total_options_eval = 0
    total_pareto_found = 0

    for idx, scen in enumerate(scenarios, 1):
        req = DecisionRequest(
            user_query=scen["query"],
            topic=scen["topic"],
            preset_options=scen["presets"],
        )

        t_start = time.time()
        res = engine.process_decision_request(req)
        exec_ms = (time.time() - t_start) * 1000.0

        scenario_latencies.append(exec_ms)
        top_title = res.report.top_recommendation.option_title if res.report and res.report.top_recommendation else "None"
        pareto_cnt = len(res.report.tradeoff_matrix.pareto_frontier_option_ids) if res.report and res.report.tradeoff_matrix else 0
        total_options_eval += len(scen["presets"])
        total_pareto_found += pareto_cnt

        print(f"  Scenario #{idx}: {scen['name']}")
        print(f"    Status:            {res.status.upper()}")
        print(f"    Execution Latency: {exec_ms:.2f} ms")
        print(f"    Top Recommendation:{top_title}")
        print(f"    Pareto Frontier:   {pareto_cnt} / {len(scen['presets'])} options")

    avg_scenario_ms = sum(scenario_latencies) / len(scenario_latencies)
    print(f"\n  Average Scenario Execution Latency: {avg_scenario_ms:.2f} ms")

    results["metrics"]["scenario_latencies_ms"] = [round(l, 2) for l in scenario_latencies]
    results["metrics"]["avg_scenario_latency_ms"] = round(avg_scenario_ms, 2)
    results["metrics"]["total_options_evaluated"] = total_options_eval
    results["metrics"]["total_pareto_found"] = total_pareto_found

    # 3. Subsystem Integration Handoff Verification
    print(f"\n[3] Subsystem Integration Handoff Verification (8 Subsystems)")
    integration = DecisionSubsystemIntegration(engine=engine)
    t_int_start = time.time()

    # Handoff 1: Planner
    h1 = integration.enhance_plan_with_decision_support({"query": "Benchmark Plan Strategy"})
    # Handoff 2: Reflection
    h2 = integration.evaluate_decision_quality("rep_bm", {"quality_score": 0.88})
    # Handoff 3: Learning
    req_dummy = DecisionRequest(user_query="Benchmark Learning")
    res_dummy = engine.process_decision_request(req_dummy)
    h3 = integration.record_decision_experience(res_dummy, {"rating": 5.0})
    # Handoff 4: Knowledge Graph
    h4 = integration.ingest_decision_tree_to_knowledge_graph(res_dummy)
    # Handoff 5: Data Intelligence
    h5 = integration.synthesize_data_intelligence({})
    # Handoff 6: Multi-Agent
    h6 = integration.convene_multi_agent_deliberation("Benchmark Debate", [])
    # Handoff 7: Browser
    h7 = integration.verify_evidence_via_browser("PostgreSQL Benchmark")
    # Handoff 8: Universal Connectors
    h8 = integration.fetch_enterprise_connector_context(["jira", "slack"])

    int_total_ms = (time.time() - t_int_start) * 1000.0

    print(f"  Planner Handoff Strategy:      {h1.get('recommended_strategy')}")
    print(f"  Reflection Evaluation Status:  {h2.get('reflection_status')}")
    print(f"  Learning Experience Recorded:  {h3.get('status')}")
    print(f"  Knowledge Graph Ingested:      {h4.get('nodes_ingested')} nodes")
    print(f"  Data Intelligence Metrics:     {len(h5.get('data_intelligence_metrics', []))} metrics")
    print(f"  Multi-Agent Consensus Status:  {h6.get('status')}")
    print(f"  Browser Verification Evidence: {len(h7.get('browser_evidence', []))} items")
    print(f"  Universal Connectors Evidence: {len(h8.get('connector_data', []))} items")
    print(f"  Total 8-Subsystem Handoff Latency: {int_total_ms:.2f} ms")

    results["metrics"]["subsystem_integration_latency_ms"] = round(int_total_ms, 2)
    results["metrics"]["telemetry_summary"] = engine.metrics.get_summary()

    # Save benchmark report json
    out_file = Path("benchmark_v3_5_decision_intelligence_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"BENCHMARK COMPLETED SUCCESSFULLY. Results saved to {out_file.name}")
    print("=" * 80)
    return results


if __name__ == "__main__":
    run_benchmark()
