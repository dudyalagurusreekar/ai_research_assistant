"""Symbol Resolver for consolidating and searching cross-reference code symbols."""

from typing import List
from tools.code.interfaces.code_interfaces import ISymbolResolver
from tools.code.models.code_models import NormalizedCodeProject, CodeSymbol
from infrastructure.logging.logger import StructuredLogger


class SymbolResolver(ISymbolResolver):
    """Aggregates and resolves symbols across all files in a NormalizedCodeProject."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("SymbolResolver")

    async def resolve_symbols(self, project: NormalizedCodeProject) -> List[CodeSymbol]:
        """Collect all symbols from project files."""
        all_symbols = []
        for file_obj in project.files:
            all_symbols.extend(file_obj.symbols)
        self._logger.info(f"Resolved {len(all_symbols)} total symbols across project '{project.project_name}'.")
        return all_symbols

    async def find_symbol(self, project: NormalizedCodeProject, name: str) -> List[CodeSymbol]:
        """Find matching symbols by name."""
        matches = []
        name_lower = name.lower()
        for file_obj in project.files:
            for sym in file_obj.symbols:
                if sym.name.lower() == name_lower:
                    matches.append(sym)
        return matches
