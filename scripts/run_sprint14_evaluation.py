"""Master CLI Runner & CI/CD Release Quality Gate Enforcer for Sprint 14."""

import argparse
import io
import os
import sys

# Force stdout/stderr to UTF-8
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.benchmark_engine import EvaluationEngine


def main():
    parser = argparse.ArgumentParser(description="ARA Sprint 14 Evaluation & Quality Assurance Platform Runner")
    parser.add_argument("--mode", choices=["fast", "full"], default="fast", help="Execution mode: 'fast' (150 sample tasks) or 'full' (all 2,600 tasks)")
    parser.add_argument("--category", type=str, default=None, help="Filter benchmark evaluation to a specific category (e.g. 'security', 'research')")
    args = parser.parse_args()

    print("=" * 80)
    print("ARA SPRINT 14 COMPREHENSIVE EVALUATION, BENCHMARK & QUALITY ASSURANCE PLATFORM")
    print("=" * 80)
    print(f" Mode:           {args.mode.upper()}")
    print(f" Category Filter: {args.category or 'ALL (15 Categories)'}")
    print("=" * 80)

    engine = EvaluationEngine()
    report = engine.run_evaluation_suite(mode=args.mode, category_filter=args.category)

    verdict = report.verdict
    metrics = report.dashboard_metrics

    print("\n" + "=" * 80)
    print("EVALUATION & BENCHMARK SUMMARY")
    print("=" * 80)
    print(f" Total Tasks Evaluated:  {metrics.total_tasks_run if metrics else 0}")
    print(f" Tasks Passed:           {metrics.passed_tasks_count if metrics else 0}")
    print(f" Tasks Failed:           {metrics.failed_tasks_count if metrics else 0}")
    print(f" Overall Pass Rate:      {metrics.overall_pass_rate if metrics else 0.0:.2f}%")
    print(f" Overall Quality Score:  {metrics.overall_quality_score if metrics else 0.0:.3f} / 1.000")
    print(f" Average Task Latency:   {metrics.avg_latency_ms if metrics else 0.0:.2f} ms")
    print("-" * 80)

    print("\nRELEASE GATE VERDICT CHECKS (11 Mandatory Gates):")
    if verdict:
        for gc in verdict.gate_checks:
            status_str = "PASSED" if gc.passed else "FAILED"
            print(f"  [{status_str:6s}] {gc.gate_name:30s}: Measured {gc.actual_value:6.2f} vs Target {gc.target_value:6.2f}")

    print("\n" + "=" * 80)
    if verdict and verdict.release_approved:
        print("VERDICT: RELEASE APPROVED - ALL QUALITY GATES PASSED 100%")
        print("=" * 80)
        sys.exit(0)
    else:
        print("VERDICT: RELEASE BLOCKED - QUALITY GATE FAILURE DETECTED")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
