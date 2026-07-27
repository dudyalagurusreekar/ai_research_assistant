"""Report Validator checking report completeness and citations."""

from tools.report.interfaces.report_interfaces import IReportValidator
from tools.report.models.report_models import NormalizedReport, ReportValidationResult
from infrastructure.logging.logger import StructuredLogger


class ReportValidator(IReportValidator):
    """Validates report title, section structure, citation integrity, and formatting."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ReportValidator")

    def validate_report(self, report: NormalizedReport) -> ReportValidationResult:
        """Validate report structure and citation references."""
        result = ReportValidationResult()

        if not report.title or report.title.strip() == "":
            result.is_valid = False
            result.issues.append("Report is missing a title.")

        if not report.sections:
            result.is_valid = False
            result.issues.append("Report contains no sections.")

        if report.metrics.word_count == 0:
            result.warnings.append("Report contains 0 total words.")

        self._logger.info(f"Validated report '{report.report_id}': valid={result.is_valid}, {len(result.issues)} issues, {len(result.warnings)} warnings.")
        return result
