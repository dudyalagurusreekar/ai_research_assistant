"""Parser Factory for the Browser Tool Subsystem.

This module provides the `ParserFactory` class, implementing the Strategy Pattern
by instantiating concrete `BaseParser` strategy implementations based on configuration settings.
"""

from typing import Dict, Type, Union, Optional

from tools.browser.config import BrowserConfig
from tools.browser.core.base_parser import BaseParser
from tools.browser.exceptions import ConfigurationError


class ParserFactory:
    """Factory for creating document parser strategy instances.

    Supports registry pattern allowing custom parser implementations to be
    registered dynamically for extension.
    """

    _registry: Dict[str, Type[BaseParser]] = {}

    @classmethod
    def register_parser(
        cls,
        name: str,
        parser_cls: Type[BaseParser],
    ) -> None:
        """Register a concrete parser implementation class.

        Args:
            name (str): Unique parser name.
            parser_cls (Type[BaseParser]): Subclass of BaseParser to register.
        """
        cls._registry[name.upper()] = parser_cls

    @classmethod
    def create_parser(
        cls,
        name: str = "BS4",
    ) -> BaseParser:
        """Instantiate and return a concrete BaseParser implementation.

        Args:
            name (str): Strategy name identifier (default: 'BS4').

        Returns:
            BaseParser: Instantiated concrete parser strategy.

        Raises:
            ConfigurationError: If requested parser strategy is unknown.
        """
        key = name.upper()

        if key not in cls._registry:
            if key in ("BS4", "LXML", "DEFAULT"):
                from tools.browser.parsers.bs4_parser import BS4Parser
                cls._registry[key] = BS4Parser
            else:
                raise ConfigurationError(
                    f"Unsupported or unregistered parser type: '{name}'. "
                    f"Available parsers: {list(cls._registry.keys())}"
                )

        parser_cls = cls._registry[key]
        return parser_cls()
