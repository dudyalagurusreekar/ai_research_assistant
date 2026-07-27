"""Static Analysis Engine inspecting code quality, complexity, and security patterns."""

import re
from typing import List, Dict, Any
from tools.code.interfaces.code_interfaces import IStaticAnalysisEngine
from tools.code.models.code_models import NormalizedCodeProject, StaticAnalysisResult
from infrastructure.logging.logger import StructuredLogger


class StaticAnalysisEngine(IStaticAnalysisEngine):
    """Engine executing static code analysis, complexity metrics, and security pattern linting."""

    SECURITY_PATTERNS = [
        (r"eval\(", "Use of eval() function poses code injection risks.", "MEDIUM"),
        (r"exec\(", "Use of exec() function poses code injection risks.", "MEDIUM"),
        (r"shell\s*=\s*True", "subprocess with shell=True poses command injection risks.", "HIGH"),
        (r"(?:api_key|password|secret)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]", "Possible hardcoded secret string detected.", "HIGH"),
    ]

    def __init__(self) -> None:
        self._logger = StructuredLogger("StaticAnalysisEngine")

    async def analyze_project(self, project: NormalizedCodeProject) -> StaticAnalysisResult:
        """Analyze project files for complexity, issues, and security warnings."""
        result = StaticAnalysisResult(
            project_id=project.project_id,
            total_files_analyzed=project.total_files,
            total_lines_of_code=project.total_lines,
        )

        total_decision_points = 0
        total_functions = 0

        for file_obj in project.files:
            lines = file_obj.content.splitlines()

            for idx, line in enumerate(lines, start=1):
                line_str = line.strip()

                # Decision points for cyclomatic complexity estimation
                if any(kw in line_str for kw in ["if ", "elif ", "for ", "while ", "except ", "case "]):
                    total_decision_points += 1

                # Security inspection
                for pat, desc, severity in self.SECURITY_PATTERNS:
                    if re.search(pat, line_str):
                        result.security_warnings.append({
                            "file": file_obj.relative_path,
                            "line": idx,
                            "severity": severity,
                            "issue": desc,
                        })

            total_functions += len([s for s in file_obj.symbols if s.symbol_type.value in ["function", "method"]])

        # Average cyclomatic complexity
        if total_functions > 0:
            result.cyclomatic_complexity = round(1.0 + (total_decision_points / total_functions), 2)

        result.metrics = {
            "total_functions": total_functions,
            "total_classes": sum(len([s for s in f.symbols if s.symbol_type.value == "class"]) for f in project.files),
            "security_warning_count": len(result.security_warnings),
        }

        self._logger.info(
            f"Analyzed project '{project.project_name}': {len(result.security_warnings)} security warnings, "
            f"complexity score {result.cyclomatic_complexity}."
        )
        return result
