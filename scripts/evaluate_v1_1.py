import os
import sys
import time
from pathlib import Path

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.research_agent import create_agent
from utils.logger import get_logger

logger = get_logger("ReleaseEvaluation")

TASKS = [
    {
        "id": "T1",
        "query": "Research the latest advancements in solid-state batteries in 2024. Summarize the key players and energy density improvements.",
    },
    {
        "id": "T2",
        "query": "Who won the Nobel Prize in Physics in 2023 and for what discovery? Please provide a detailed summary.",
    }
]

def run_evaluation():
    logger.info("Starting ARA v1.1 Release Evaluation Suite")
    results = []
    
    agent = create_agent()
    
    for task in TASKS:
        logger.info(f"Executing Task {task['id']}: {task['query']}")
        start_time = time.time()
        
        try:
            response = agent.run(task["query"])
            latency = time.time() - start_time
            
            # Simple check if self-verification/confidence score is in the response string
            report_verified = "yes" if "Confidence" in str(response) or "Executive Summary" in str(response) else "unknown"
            
            # We can extract steps from agent.memory if we need tool_calls, but we'll leave it simple for now
            # since the agent clears its memory/steps across runs sometimes or we can inspect agent.logs
            
            results.append({
                "task_id": task["id"],
                "query": task["query"],
                "status": "Success",
                "latency_s": round(latency, 2),
                "tool_calls": "N/A",  # Could be derived from agent.memory.steps
                "errors": 0,
                "verified": report_verified,
                "output": str(response)[:500] + "..." # Truncate for report
            })
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"Task {task['id']} failed: {e}", exc_info=True)
            results.append({
                "task_id": task["id"],
                "query": task["query"],
                "status": "Failed",
                "error": str(e),
                "latency_s": round(latency, 2)
            })

    generate_markdown_report(results)

def generate_markdown_report(results):
    report_path = Path("benchmark_report.md")
    lines = [
        "# ARA v1.1 Evaluation & Benchmark Report",
        "",
        "## Executive Summary",
        "This report contains the results of the automated end-to-end evaluation for the AI Research Assistant Version 1.1 release.",
        "",
        "## Task Results",
        ""
    ]
    
    success_count = sum(1 for r in results if r["status"] == "Success")
    lines.append(f"**Total Tasks:** {len(results)}")
    lines.append(f"**Success Rate:** {success_count}/{len(results)} ({(success_count/len(results))*100:.1f}%)")
    lines.append("")
    
    lines.append("| Task ID | Status | Latency (s) | Tool Calls | Errors | Verified |")
    lines.append("|---------|--------|-------------|------------|--------|----------|")
    
    for r in results:
        status = r["status"]
        latency = r.get("latency_s", "N/A")
        tools = r.get("tool_calls", "N/A")
        errors = r.get("errors", "N/A")
        verified = r.get("verified", "N/A")
        
        lines.append(f"| {r['task_id']} | {status} | {latency} | {tools} | {errors} | {verified} |")
        
    lines.append("")
    lines.append("## Detailed Outputs")
    for r in results:
        lines.append(f"### Task {r['task_id']}")
        lines.append(f"**Query:** {r['query']}")
        if r["status"] == "Success":
            lines.append(f"**Output Snippet:**\n```\n{r['output']}\n```")
        else:
            lines.append(f"**Error:**\n```\n{r.get('error', 'Unknown')}\n```")
        lines.append("")
        
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Benchmark report generated at {report_path.absolute()}")

if __name__ == "__main__":
    run_evaluation()
