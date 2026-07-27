"""Memory Provider Strategy Registry implementation."""

from typing import Dict, List, Optional
from tools.memory.interfaces.memory_interfaces import IMemoryProvider, IMemoryRegistry
from tools.memory.models.memory_models import MemoryType
from infrastructure.logging.logger import StructuredLogger


class MemoryRegistry(IMemoryRegistry):
    """Registry maintaining mappings between MemoryType enums and concrete IMemoryProvider instances."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("MemoryRegistry")
        self._providers: Dict[MemoryType, IMemoryProvider] = {}

    def register(self, provider: IMemoryProvider) -> None:
        """Register a provider for its memory type."""
        self._providers[provider.memory_type] = provider
        self._logger.debug(f"Registered memory provider '{provider.__class__.__name__}' for type '{provider.memory_type.value}'")

    def get_provider(self, memory_type: MemoryType) -> Optional[IMemoryProvider]:
        """Retrieve provider strategy by MemoryType."""
        return self._providers.get(memory_type)

    def list_providers(self) -> List[IMemoryProvider]:
        """List all registered memory providers."""
        return list(self._providers.values())
