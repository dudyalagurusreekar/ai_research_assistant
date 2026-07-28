import os
import sys
import time
import io
from pathlib import Path

# Use gemini-3-flash-preview as the starting model
os.environ["MODEL_NAME"] = "gemini/gemini-3-flash-preview"

# Set max output tokens to 4096 to prevent truncation syntax errors
os.environ["MODEL_MAX_TOKENS"] = "4096"

# Force stdout and stderr to use UTF-8 to prevent Windows cp1252 console encoding crashes
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Monkey-patch LiteLLM resilience modules to handle free-tier Gemini limits gracefully
import utils.resilience.client as resilience_client
import utils.resilience.errors as resilience_errors

# 1. Modify the fallback registry to fallback across working models
resilience_client.registry.default_fallbacks = [
    "gemini/gemini-3-flash-preview",
    "gemini/gemini-3.1-flash-lite",
    "gemini/gemini-2.5-flash-lite",
]

# 2. Reclassify temporary QuotaExceeded as RateLimit, but keep daily QuotaExceeded permanent
original_classify_exception = resilience_errors.classify_exception

def custom_classify_exception(exc: Exception) -> resilience_errors.LLMResilienceError:
    classified = original_classify_exception(exc)
    exc_msg = str(exc).lower()
    
    # If it is a daily quota limit, return QuotaExceededError so the client triggers immediate failover
    if "perday" in exc_msg or "per day" in exc_msg or "daily" in exc_msg:
        print("Daily quota limit hit. Triggering immediate model failover...", flush=True)
        return resilience_errors.QuotaExceededError(str(exc))
        
    # If it is a temporary per-minute rate limit, classify as RateLimitError so we retry
    if isinstance(classified, resilience_errors.QuotaExceededError):
        return resilience_errors.RateLimitError(str(exc))
        
    return classified

resilience_errors.classify_exception = custom_classify_exception

# 3. Intercept resilient_completion to enforce 6s sleep on success and sleep 65s on rate limits
original_resilient_completion = resilience_client.resilient_completion

def rate_limited_resilient_completion(*args, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Clear circuit breaker to prevent cooldown locks
            if hasattr(resilience_client, "circuit_breaker") and resilience_client.circuit_breaker:
                resilience_client.circuit_breaker.healths.clear()
            
            res = original_resilient_completion(*args, **kwargs)
            # Sleep 6 seconds to stay comfortably below 15 RPM
            print("Completed LLM request successfully. Enforcing rate limit delay (6s)...", flush=True)
            time.sleep(6)
            return res
        except Exception as e:
            err_str = str(e).lower()
            
            # If it's a daily limit or non-rate-limit exception, raise it immediately to trigger failover
            if "perday" in err_str or "per day" in err_str or "daily" in err_str:
                raise e
                
            # If it's a temporary rate limit or circuit issue, sleep 65s and retry
            if any(term in err_str for term in ["quota", "limit", "exhausted", "429", "circuit", "failover", "failed"]):
                print(f"Temporary rate limit hit: {e}. Sleeping 65 seconds before retry {attempt+1}/{max_retries}...", flush=True)
                time.sleep(65)
                # Clear circuit breaker so retry attempts don't get blocked
                if hasattr(resilience_client, "circuit_breaker") and resilience_client.circuit_breaker:
                    resilience_client.circuit_breaker.healths.clear()
            else:
                # Raise other exceptions immediately
                raise e
    raise Exception("Resilient completion rate-limit retries exhausted.")

resilience_client.resilient_completion = rate_limited_resilient_completion

from agents.research_agent import create_agent
from utils.logger import get_logger

logger = get_logger("ReleaseEvaluation")

# Define our 7 test scenarios
TASKS = [
    {
        "id": "T1",
        "category": "Multi-source Web Research",
        "query": "Research the latest advancements in solid-state batteries in 2024. Summarize the key players and energy density improvements.",
    },
    {
        "id": "T2",
        "category": "QA & Fact Verification",
        "query": "Who won the Nobel Prize in Physics in 2023 and for what discovery? Provide a detailed summary.",
    },
    {
        "id": "T3",
        "category": "Document Processing",
        "query": "Read the local file ReleaseNotes_v1.1.md and summarize the key enhancements introduced in version 1.1.",
    },
    {
        "id": "T4",
        "category": "Memory Platform Integration",
        "query": "Using memory_tool, store the fact 'Project ARA V1.1 test date is July 28, 2026'. Then recall this information and print it.",
    },
    {
        "id": "T5",
        "category": "Code Intelligence & Sandbox",
        "query": "Using code_tool with action 'execute', run a Python snippet that prints the first 5 Fibonacci numbers, and print the output.",
    },
    {
        "id": "T6",
        "category": "Report Gen & Validation",
        "query": "Using document_tool with action 'summarize', summarize the local file README.md, and then validate the report structure using report_tool with action 'validate'.",
    },
    {
        "id": "T7",
        "category": "Failure Recovery & Resilience",
        "query": "Attempt to perform a search for a broken web url like 'https://this-domain-does-not-exist-at-all-12345.xyz' and verify that the system gracefully handles the failure.",
    }
]

def run_evaluation():
    logger.info("Starting ARA v1.1 Release Evaluation Suite")
    results = []
    
    # Create the agent
    agent = create_agent()
    
    for task in TASKS:
        logger.info(f"Executing Task {task['id']} [{task['category']}]: {task['query']}")
        start_time = time.time()
        
        try:
            response = agent.run(task["query"])
            latency = time.time() - start_time
            
            # Count tool calls and get list of tools called in this run
            tool_calls_count = 0
            tools_used = []
            if hasattr(agent, "memory") and hasattr(agent.memory, "steps"):
                for step in agent.memory.steps:
                    if hasattr(step, "tool_calls") and step.tool_calls:
                        for tc in step.tool_calls:
                            tool_calls_count += 1
                            name = tc.name if hasattr(tc, "name") else (tc.get("name") if isinstance(tc, dict) else str(tc))
                            if name not in tools_used:
                                tools_used.append(name)
                    elif hasattr(step, "action") and step.action:
                        tool_calls_count += 1
                        act = str(step.action)
                        if act not in tools_used:
                            tools_used.append(act)
            
            tool_calls_str = ", ".join(tools_used) if tools_used else "None"
            
            # Simple check if self-verification/confidence score is in the response string
            report_verified = "yes" if "Confidence" in str(response) or "Executive Summary" in str(response) or "is_valid" in str(response) else "unknown"
            
            results.append({
                "task_id": task["id"],
                "category": task["category"],
                "query": task["query"],
                "status": "Success",
                "latency_s": round(latency, 2),
                "tool_calls": tool_calls_count,
                "tools_used": tool_calls_str,
                "errors": 0,
                "verified": report_verified,
                "output": str(response)
            })
            logger.info(f"Task {task['id']} completed successfully in {latency:.2f}s")
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"Task {task['id']} failed: {e}", exc_info=True)
            results.append({
                "task_id": task["id"],
                "category": task["category"],
                "query": task["query"],
                "status": "Failed",
                "latency_s": round(latency, 2),
                "tool_calls": 0,
                "tools_used": "N/A",
                "errors": 1,
                "verified": "no",
                "error": str(e)
            })
            
    generate_markdown_report(results)

def generate_markdown_report(results):
    report_path = Path("benchmark_report.md")
    lines = [
        "# ARA v1.1 Evaluation & Benchmark Report",
        "",
        "## Executive Summary",
        "This report contains the results of the automated end-to-end evaluation for the AI Research Assistant Version 1.1 release across 7 key test scenarios.",
        "",
        "## Test Scenarios Summary",
        ""
    ]
    
    success_count = sum(1 for r in results if r["status"] == "Success")
    total_tasks = len(results)
    success_rate = (success_count / total_tasks) * 100 if total_tasks > 0 else 0
    
    lines.append(f"**Total Scenarios:** {total_tasks}")
    lines.append(f"**Success Rate:** {success_count}/{total_tasks} ({success_rate:.1f}%)")
    lines.append("")
    
    lines.append("| Task ID | Category | Status | Latency (s) | Tool Calls | Tools Used | Verified |")
    lines.append("|---------|----------|--------|-------------|------------|------------|----------|")
    
    for r in results:
        status = r["status"]
        latency = r.get("latency_s", "N/A")
        tools = r.get("tool_calls", 0)
        tools_used = r.get("tools_used", "None")
        verified = r.get("verified", "unknown")
        
        lines.append(f"| {r['task_id']} | {r['category']} | {status} | {latency} | {tools} | {tools_used} | {verified} |")
        
    lines.append("")
    lines.append("## Detailed Outputs")
    for r in results:
        lines.append(f"### Task {r['task_id']} - {r['category']}")
        lines.append(f"**Query:** {r['query']}")
        if r["status"] == "Success":
            out_snippet = r['output']
            if len(out_snippet) > 800:
                out_snippet = out_snippet[:800] + "\n... [TRUNCATED] ..."
            lines.append(f"**Output Snippet:**\n```\n{out_snippet}\n```")
        else:
            lines.append(f"**Error:**\n```\n{r.get('error', 'Unknown')}\n```")
        lines.append("")
        
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Benchmark report generated at {report_path.absolute()}")

if __name__ == "__main__":
    run_evaluation()
