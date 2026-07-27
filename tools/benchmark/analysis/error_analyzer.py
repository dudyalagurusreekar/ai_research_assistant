"""Error Analyzer classifying task failure taxonomy."""

from typing import Optional
from tools.benchmark.interfaces.benchmark_interfaces import IErrorAnalyzer
from tools.benchmark.models.benchmark_models import ErrorCategory, ExecutionTrace
from infrastructure.logging.logger import StructuredLogger


class ErrorAnalyzer(IErrorAnalyzer):
    """Classifies task failure modes into ErrorCategory taxonomy."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ErrorAnalyzer")

    def classify_error(self, predicted: str, ground_truth: str, trace: Optional[ExecutionTrace] = None) -> ErrorCategory:
        """Classify failure mode."""
        if not predicted or predicted.strip() == "":
            return ErrorCategory.PLANNING

        if trace and trace.tool_invocations:
            invoked = [t.lower() for t in trace.tool_invocations]
            if "browser_tool" in invoked:
                return ErrorCategory.BROWSER
            elif "vision_tool" in invoked:
                return ErrorCategory.VISION
            elif "code_tool" in invoked:
                return ErrorCategory.CODE
            elif "search_tool" in invoked:
                return ErrorCategory.SEARCH

        return ErrorCategory.REASONING
