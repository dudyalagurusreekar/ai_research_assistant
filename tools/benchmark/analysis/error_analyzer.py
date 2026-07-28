"""Failure Analyzer classifying task failures across 16 categories with root-cause identification."""

from typing import Optional
from tools.benchmark.interfaces.benchmark_interfaces import IFailureAnalyzer
from tools.benchmark.models.benchmark_models import (
    GAIATask,
    ErrorCategory,
    ExecutionTrace,
    FailureReport,
)
from infrastructure.logging.logger import StructuredLogger


class FailureAnalyzer(IFailureAnalyzer):
    """Automatically classifies benchmark task failures into 16 taxonomy categories and generates diagnostic root cause reports."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("FailureAnalyzer")

    def classify_error(
        self, predicted: str, ground_truth: str, trace: Optional[ExecutionTrace] = None
    ) -> ErrorCategory:
        """Classify failure mode into ErrorCategory taxonomy."""
        report = self.generate_failure_report(
            task=GAIATask(ground_truth=ground_truth),
            predicted=predicted,
            trace=trace,
        )
        return report.error_category

    def generate_failure_report(
        self, task: GAIATask, predicted: str, trace: Optional[ExecutionTrace] = None
    ) -> FailureReport:
        """Generate detailed failure report with probable root cause analysis."""
        task_id = task.task_id if task else ""

        # 1. Empty or missing prediction -> Planning / Timeout / Infrastructure
        if not predicted or not predicted.strip():
            if trace and any("timeout" in err.lower() for err in trace.error_propagation):
                return FailureReport(
                    task_id=task_id,
                    error_category=ErrorCategory.TIMEOUT,
                    probable_root_cause="Execution timed out before completing response generation.",
                    step_index=len(trace.steps) - 1 if trace and trace.steps else -1,
                )
            return FailureReport(
                task_id=task_id,
                error_category=ErrorCategory.PLANNING,
                probable_root_cause="Agent failed to formulate an execution plan or produce an answer.",
                step_index=0,
            )

        # 2. Inspect trace step errors or tool invocations
        if trace:
            # Check step errors
            for idx, step_dict in enumerate(trace.steps):
                err_msg = str(step_dict.get("error", "")).lower()
                tool = str(step_dict.get("tool_name", "")).lower()
                step_type = str(step_dict.get("step_type", "")).lower()

                if "timeout" in err_msg or "time out" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.TIMEOUT,
                        probable_root_cause=f"Step {idx} ({tool or step_type}) timed out.",
                        step_index=idx,
                    )
                if "connection" in err_msg or "network" in err_msg or "server" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.INFRASTRUCTURE,
                        probable_root_cause=f"Infrastructure connectivity failure in step {idx}: {err_msg}",
                        step_index=idx,
                    )
                if "browser" in tool or "playwright" in err_msg or "element not found" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.BROWSER,
                        probable_root_cause=f"Browser DOM navigation or element interaction failed in step {idx}: {err_msg}",
                        step_index=idx,
                    )
                if "ocr" in tool or "tesseract" in err_msg or "text extraction" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.OCR,
                        probable_root_cause=f"OCR text extraction failed in step {idx}.",
                        step_index=idx,
                    )
                if "vision" in tool or "image" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.VISION,
                        probable_root_cause=f"Multimodal vision processing failure in step {idx}.",
                        step_index=idx,
                    )
                if "code" in tool or "syntaxerror" in err_msg or "traceback" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.CODE_EXECUTION,
                        probable_root_cause=f"Code execution runtime/syntax error in step {idx}: {err_msg}",
                        step_index=idx,
                    )
                if "search" in tool or "query" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.SEARCH,
                        probable_root_cause=f"Search retrieval produced irrelevant or empty results in step {idx}.",
                        step_index=idx,
                    )
                if "document" in tool or "pdf" in err_msg or "parse" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.DOCUMENT_PARSING,
                        probable_root_cause=f"Document parsing failure in step {idx}.",
                        step_index=idx,
                    )
                if "memory" in tool or "vector" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.MEMORY_RETRIEVAL,
                        probable_root_cause=f"Memory context retrieval miss in step {idx}.",
                        step_index=idx,
                    )
                if "integration" in tool or "api" in err_msg:
                    return FailureReport(
                        task_id=task_id,
                        error_category=ErrorCategory.EXTERNAL_INTEGRATION,
                        probable_root_cause=f"External API integration failure in step {idx}.",
                        step_index=idx,
                    )

            # Check tool invocation taxonomy if no explicit error in steps
            invoked = [t.lower() for t in trace.tool_invocations]
            if not invoked:
                return FailureReport(
                    task_id=task_id,
                    error_category=ErrorCategory.TOOL_SELECTION,
                    probable_root_cause="No tools were selected or invoked to solve the task.",
                    step_index=0,
                )
            if "browser_tool" in invoked:
                return FailureReport(
                    task_id=task_id,
                    error_category=ErrorCategory.BROWSER,
                    probable_root_cause="Browser tool action did not reach target information.",
                    step_index=-1,
                )
            if "vision_tool" in invoked:
                return FailureReport(
                    task_id=task_id,
                    error_category=ErrorCategory.VISION,
                    probable_root_cause="Vision tool failed to accurately read multi-modal artifacts.",
                    step_index=-1,
                )
            if "code_tool" in invoked:
                return FailureReport(
                    task_id=task_id,
                    error_category=ErrorCategory.CODE_EXECUTION,
                    probable_root_cause="Code tool output differed from ground truth calculation.",
                    step_index=-1,
                )
            if "search_tool" in invoked:
                return FailureReport(
                    task_id=task_id,
                    error_category=ErrorCategory.SEARCH,
                    probable_root_cause="Search strategy failed to locate exact ground truth fact.",
                    step_index=-1,
                )

        # 3. Check for formatting errors (e.g. correct answer hidden in verbose text)
        if task and task.ground_truth and task.ground_truth.lower() in predicted.lower():
            return FailureReport(
                task_id=task_id,
                error_category=ErrorCategory.FORMATTING,
                probable_root_cause="Correct answer was present in response but failed GAIA formatting validation.",
                step_index=-1,
            )

        # Default fallback -> Multi-step reasoning failure
        return FailureReport(
            task_id=task_id,
            error_category=ErrorCategory.REASONING,
            probable_root_cause="Multi-step reasoning deduction failed to match ground truth answer.",
            step_index=-1,
        )


# Alias for backward compatibility
ErrorAnalyzer = FailureAnalyzer
