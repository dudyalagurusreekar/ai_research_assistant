"""Vision Provider Strategy Registry implementation."""

from typing import Dict, List, Optional
from tools.vision.interfaces.vision_interfaces import IVisionProvider, IVisionProviderRegistry
from infrastructure.logging.logger import StructuredLogger


class VisionProviderRegistry(IVisionProviderRegistry):
    """Registry maintaining mappings between provider names and IVisionProvider strategy instances."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("VisionProviderRegistry")
        self._providers: Dict[str, IVisionProvider] = {}

    def register(self, provider: IVisionProvider) -> None:
        """Register a vision provider strategy."""
        name = provider.provider_name.lower()
        self._providers[name] = provider
        self._logger.debug(f"Registered vision provider '{provider.provider_name}'")

    def get_provider(self, name: str) -> Optional[IVisionProvider]:
        """Retrieve registered provider strategy by name."""
        return self._providers.get(name.lower())

    def list_providers(self) -> List[IVisionProvider]:
        """List all registered vision providers."""
        return list(self._providers.values())
