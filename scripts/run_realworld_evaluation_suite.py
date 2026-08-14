#!/usr/bin/env python3
"""Run the Real-World Evaluation Suite (10 Production Tasks) and generate all reports and scorecards."""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.evaluation.realworld_suite import RealWorldEvaluationSuite
from utils.logger import get_logger

logger = get_logger("RunRealWorldSuite")


def main() -> int:
    print("=" * 80)
    print(" ARA Version 3.0 — Real-World Evaluation Suite Execution (10 Tasks)")
    print("=" * 80)

    suite = RealWorldEvaluationSuite()
    result = suite.execute_suite()

    print("\n" + "=" * 80)
    print(f" EXECUTION COMPLETED: {len(result.results)} / 10 Tasks Completed")
    print(f" Total Score: {result.total_score:.1f} / {result.max_score:.1f} ({result.average_score:.1f}%)")
    print(f" Total Latency: {result.total_latency_ms:.2f} ms")
    print(f" Master Scorecard Written To: reports/evaluation/MASTER_EVALUATION_SCORECARD.md")
    print("=" * 80)

    return 0 if result.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
