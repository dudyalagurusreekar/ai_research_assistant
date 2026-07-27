"""Dynamic Search Provider Registry implementation."""

from typing import Dict, List, Optional
from tools.search.interfaces.provider import ISearchProvider, ISearchProviderRegistry
from infrastructure.logging.logger import StructuredLogger


class SearchProviderRegistry(ISearchProviderRegistry):
    """Registry maintaining available ISearchProvider strategy instances."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("SearchProviderRegistry")
        self._providers: Dict[str, ISearchProvider] = {}

    def register(self, provider: ISearchProvider) -> None:
        """Register a search provider strategy."""
        name = provider.provider_name.lower()
        self._providers[name] = provider
        self._logger.debug(f"Registered search provider '{provider.provider_name}'")

    def get_provider(self, name: str) -> Optional[ISearchProvider]:
        """Retrieve registered provider by name."""
        return self._providers.get(name.lower())

    def list_providers(self) -> List[ISearchProvider]:
        """List all registered search providers."""
        return list(self._providers.values())

    def get_providers_for_intent(self, intent_val: str) -> List[ISearchProvider]:
        """Get all providers matching a given intent."""
        result = []
        for p in self._providers.values():
            if intent_val.lower() in [i.lower() for i in p.supported_intents]:
                result.append(p)
        return result
