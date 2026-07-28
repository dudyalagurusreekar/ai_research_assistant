"""Submission Generator creating official GAIA jsonl submission files with schema validation."""

import os
import json
from typing import List, Optional
from tools.benchmark.interfaces.benchmark_interfaces import ISubmissionGenerator
from tools.benchmark.models.benchmark_models import (
    NormalizedBenchmarkResult,
    SubmissionEntry,
    SubmissionPackage,
)
from tools.benchmark.formatter.answer_formatter import AnswerFormatter
from infrastructure.logging.logger import StructuredLogger


class SubmissionGenerator(ISubmissionGenerator):
    """Generates and validates official GAIA benchmark jsonl submission files."""

    def __init__(self, formatter: Optional[AnswerFormatter] = None) -> None:
        self._logger = StructuredLogger("SubmissionGenerator")
        self._formatter = formatter or AnswerFormatter()

    def generate_submission(
        self, results: List[NormalizedBenchmarkResult], output_file: str
    ) -> SubmissionPackage:
        """Generate official GAIA jsonl submission file from benchmark results."""
        package = SubmissionPackage(total_tasks=len(results))
        seen_ids = set()

        for res in results:
            if not res.task_id:
                package.validation_errors.append("Encountered result entry with missing task_id.")
                package.is_valid = False
                continue

            if res.task_id in seen_ids:
                package.validation_errors.append(f"Duplicate task_id '{res.task_id}' detected in submission.")
                package.is_valid = False
            seen_ids.add(res.task_id)

            # Format answer prior to export
            formatted_ans = self._formatter.format_answer(res.predicted_answer)

            # Validate answer formatting
            if not self._formatter.validate_format(formatted_ans):
                package.validation_errors.append(
                    f"Task '{res.task_id}' answer failed formatting validation: '{formatted_ans}'"
                )

            trace_summary = None
            if res.trace:
                trace_summary = f"ExecTime: {res.trace.execution_time_ms}ms, Tools: {', '.join(res.trace.tool_invocations)}"

            entry = SubmissionEntry(
                task_id=res.task_id,
                model_answer=formatted_ans,
                reasoning_trace=trace_summary,
            )
            package.entries.append(entry)

        # Write to JSONL file if valid or if forced
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                for entry in package.entries:
                    f.write(json.dumps(entry.to_dict()) + "\n")

            self._logger.info(
                f"Generated submission file '{output_file}' with {len(package.entries)} entries (valid={package.is_valid})"
            )
        except Exception as e:
            package.is_valid = False
            package.validation_errors.append(f"Failed to write submission file: {str(e)}")
            self._logger.error(f"Error writing submission file '{output_file}': {e}")

        return package
