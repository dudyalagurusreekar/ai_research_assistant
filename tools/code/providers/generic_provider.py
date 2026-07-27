"""Generic Language Provider fallback strategy implementation."""

import re
import os
from typing import List
from tools.code.interfaces.code_interfaces import ILanguageProvider
from tools.code.models.code_models import CodeFile, CodeSymbol, SymbolType
from infrastructure.logging.logger import StructuredLogger


class GenericLanguageProvider(ILanguageProvider):
    """Fallback strategy for Java, Go, C/C++, Rust, and unclassified text code files."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("GenericLanguageProvider")

    @property
    def language_name(self) -> str:
        return "generic"

    @property
    def file_extensions(self) -> List[str]:
        return [".java", ".go", ".c", ".cpp", ".h", ".rs", ".sh", ".bat", ".yaml", ".json"]

    async def parse_file(self, file_path: str, content: str) -> CodeFile:
        """Parse generic file using regex heuristic symbol discovery."""
        ext = os.path.splitext(file_path)[1].lower()
        lines = content.splitlines()
        file_obj = CodeFile(
            relative_path=file_path,
            absolute_path=file_path,
            language=ext.lstrip(".") or "text",
            size_bytes=len(content.encode("utf-8")),
            line_count=len(lines),
            content=content,
        )

        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()

            # Class or struct definitions
            type_match = re.search(r"(?:class|struct|interface|type)\s+([A-Za-z0-9_$]+)", line_str)
            if type_match:
                file_obj.symbols.append(
                    CodeSymbol(
                        name=type_match.group(1),
                        symbol_type=SymbolType.CLASS if "class" in line_str or "struct" in line_str else SymbolType.INTERFACE,
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        signature=type_match.group(0),
                    )
                )

            # Function / Method signatures
            func_match = re.search(r"(?:func|fn|public|private|def)\s+([A-Za-z0-9_$]+)\s*\(", line_str)
            if func_match:
                file_obj.symbols.append(
                    CodeSymbol(
                        name=func_match.group(1),
                        symbol_type=SymbolType.FUNCTION,
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        signature=func_match.group(0),
                    )
                )

        return file_obj
