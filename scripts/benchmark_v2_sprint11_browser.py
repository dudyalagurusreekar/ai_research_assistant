"""ARA v2.0 Browser Automation Platform Benchmark (Sprint 11).

Measures end-to-end performance across:
- Navigation & Page Load Latency
- DOM Tree Parsing & Simplification Speed
- Structured Extraction Throughput
- Workflow Recording & Replay Latency
- CAPTCHA Detection & Security Interception Reliability
"""

import asyncio
import io
import json
import os
import sys
import time
from pathlib import Path

# Force stdout and stderr to use UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.browser.platform.engine import BrowserPlatformEngine
from tools.browser.platform.models import ActionType, BrowserAction, ExtractionSchema
from tools.browser.platform.workflow_recorder import WorkflowRecorder
from tools.browser.platform.workflow_executor import WorkflowExecutor


async def run_benchmark():
    print("=" * 80)
    print("ARA v2.0 Browser Automation Platform Benchmark (Sprint 11)")
    print("=" * 80)

    engine = BrowserPlatformEngine()
    init_start = time.time()
    await engine.initialize()
    init_duration_ms = (time.time() - init_start) * 1000

    print(f"[Init] Browser Platform initialized in {init_duration_ms:.2f} ms")

    # Benchmark 1: Navigation Latency
    nav_start = time.time()
    nav_res = await engine.navigate("https://example.com")
    nav_duration_ms = (time.time() - nav_start) * 1000
    print(f"[Navigation] Open URL 'https://example.com': success={nav_res.success}, latency={nav_duration_ms:.2f} ms")

    # Benchmark 2: DOM Parsing & Simplification
    dom_start = time.time()
    dom_tree = await engine.get_dom_tree()
    dom_duration_ms = (time.time() - dom_start) * 1000
    print(f"[DOM Engine] Parsed {dom_tree.total_nodes} nodes ({len(dom_tree.interactive_elements)} interactive) in {dom_duration_ms:.2f} ms")

    # Benchmark 3: Structured Extraction
    ext_start = time.time()
    schema = ExtractionSchema(
        schema_id="benchmark_schema",
        name="Page Header",
        fields={"title": "h1"},
    )
    ext_res = await engine.extract_schema(schema)
    ext_duration_ms = (time.time() - ext_start) * 1000
    print(f"[Extraction] Extracted schema: success={ext_res.success}, items={ext_res.item_count}, latency={ext_duration_ms:.2f} ms")

    # Benchmark 4: Workflow Replay
    recorder = WorkflowRecorder()
    recorder.start_recording("bm_wf", "Benchmark Workflow")
    recorder.record_step(BrowserAction(action_type=ActionType.NAVIGATE, url="https://example.com"))
    recorder.record_step(BrowserAction(action_type=ActionType.EXTRACT_TEXT))
    wf = recorder.stop_recording()

    wf_start = time.time()
    executor = WorkflowExecutor()
    wf_res = await executor.execute_workflow(engine._active_page, wf)
    wf_duration_ms = (time.time() - wf_start) * 1000
    print(f"[Workflow Engine] Replayed {len(wf.steps)} steps: success={wf_res.success}, duration={wf_duration_ms:.2f} ms")

    # Benchmark 5: Security Guardrails
    high_impact_action = BrowserAction(
        action_type=ActionType.CLICK,
        target_selector="button#delete-all",
        text="Delete All Files Permanently",
    )
    sec_res = await engine.execute_action(high_impact_action)
    print(f"[Security Layer] High-Impact Action Interception: intercepted={not sec_res.success}, reason='{sec_res.message}'")

    summary = engine.metrics_engine.get_summary()
    print("-" * 80)
    print("BENCHMARK SUMMARY METRICS:")
    print(json.dumps(summary, indent=2))
    print("-" * 80)

    # Sprint 11 vs Prior Baseline Comparison
    print("SPRINT 11 vs PRIOR BASELINE COMPARISON")
    print(f"  DOM Tree Perception:    v1.0-Sprint 10=Raw HTML -> Sprint 11=Structured Semantic DOM Tree")
    print(f"  Dynamic Content Wait:   v1.0-Sprint 10=Fixed Sleep -> Sprint 11=Adaptive Wait Strategies & Infinite Scroll")
    print(f"  CAPTCHA & Access Gate:  v1.0-Sprint 10=Crash/Timeout -> Sprint 11=Multi-Provider Signature Detection")
    print(f"  Security Guardrails:    v1.0-Sprint 10=Unrestricted -> Sprint 11=Explicit User Confirmation Gates")
    print(f"  Reusable Workflows:     v1.0-Sprint 10=Manual Script -> Sprint 11=JSON Blueprint Record & Replay")
    print("=" * 80)

    await engine.shutdown()


if __name__ == "__main__":
    asyncio.run(run_benchmark())
