"""Language Strategy Registry implementation."""

import os
from typing import Dict, List, Optional
from tools.code.interfaces.code_interfaces import ILanguageProvider, ILanguageRegistry
from tools.code.providers.python_provider import PythonLanguageProvider
from tools.code.providers.js_provider import JavaScriptLanguageProvider
from tools.code.providers.generic_provider import GenericLanguageProvider
from infrastructure.logging.logger import StructuredLogger


class LanguageRegistry(ILanguageRegistry):
    """Registry maintaining mappings between file extensions and concrete ILanguageProvider strategies."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("LanguageRegistry")
        self._ext_map: Dict[str, ILanguageProvider] = {}
        self._default_provider = GenericLanguageProvider()

        # Register default language providers
        self.register(PythonLanguageProvider())
        self.register(JavaScriptLanguageProvider())
        self.register(self._default_provider)

    def register(self, provider: ILanguageProvider) -> None:
        """Register a language strategy for its supported file extensions."""
        for ext in provider.file_extensions:
            self._ext_map[ext.lower()] = provider
            self._logger.debug(f"Registered language provider '{provider.language_name}' for extension '{ext}'")

    def get_provider_for_extension(self, ext: str) -> Optional[ILanguageProvider]:
        """Retrieve provider strategy for a file extension."""
        clean_ext = f".{ext.lstrip('.')}".lower()
        return self._ext_map.get(clean_ext, self._default_provider)
