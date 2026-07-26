"""Unified Central Automated Test Runner for AI Research Assistant.

Discovers all test cases in the 'tests' directory, executes them sequentially,
captures stress and performance metrics, compiles a results report, and exits
with an appropriate return status code.
"""

import sys
from pathlib import Path
import unittest
import time

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def run_test_suite() -> int:
    """Discover and run all project unit, integration, stress, and performance tests."""
    print("==========================================================")
    print("      AI Research Assistant - Automated Test Runner       ")
    print("==========================================================")

    start_time = time.time()
    
    # 1. Discover all tests in tests/
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")

    # 2. Run the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    elapsed_seconds = time.time() - start_time

    print("\n==========================================================")
    print("                      Test Summary                       ")
    print("==========================================================")
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Total Duration:  {elapsed_seconds:.2f} seconds")
    print(f"Success Status:  {result.wasSuccessful()}")
    print(f"Failures:        {len(result.failures)}")
    print(f"Errors:          {len(result.errors)}")

    if not result.wasSuccessful():
        print("\nFailures Details:")
        for test, traceback in result.failures + result.errors:
            print(f"- {test.id()} failed.")
        return 1

    print("\nAll tests completed successfully. Zero regressions found!")
    return 0


if __name__ == "__main__":
    sys.exit(run_test_suite())
