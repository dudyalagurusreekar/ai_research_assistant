"""Base Service Interface for lifecycle-managed infrastructure components."""

from abc import ABC, abstractmethod


class IService(ABC):
    """Lifecycle interface for core system services."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service resources."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown and cleanup service resources."""
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Return True if service is initialized and operational."""
        pass
