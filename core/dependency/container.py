"""Dependency Injection Container implementation."""

from enum import Enum, auto
from typing import Any, Callable, Dict, Type, TypeVar, Optional
from core.exceptions.base import DependencyError
from core.exceptions.codes import ErrorCode

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Lifetime management for registered services."""

    SINGLETON = auto()
    TRANSIENT = auto()


class _ServiceDescriptor:

    def __init__(
        self,
        service_type: Type[Any],
        lifetime: ServiceLifetime,
        instance: Optional[Any] = None,
        factory: Optional[Callable[["DependencyContainer"], Any]] = None,
    ) -> None:
        self.service_type = service_type
        self.lifetime = lifetime
        self.instance = instance
        self.factory = factory


class DependencyContainer:
    """Inversion of Control (IoC) Dependency Injection Container.

    Supports registering instances, factories, singletons, and transient services.
    """

    def __init__(self) -> None:
        self._descriptors: Dict[Type[Any], _ServiceDescriptor] = {}

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a pre-constructed singleton instance.

        Args:
            service_type: Type or Interface ABC.
            instance: Instantiated object.
        """
        if not isinstance(instance, service_type):
            raise DependencyError(
                f"Instance {instance} is not an instance of {service_type.__name__}",
                code=ErrorCode.DEPENDENCY_RESOLUTION_FAILED,
            )
        self._descriptors[service_type] = _ServiceDescriptor(
            service_type=service_type,
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance,
        )

    def register_singleton(
        self,
        service_type: Type[T],
        factory: Callable[["DependencyContainer"], T],
    ) -> None:
        """Register a factory function that will be executed once to produce a singleton.

        Args:
            service_type: Type or Interface ABC.
            factory: Callable producing the service.
        """
        self._descriptors[service_type] = _ServiceDescriptor(
            service_type=service_type,
            lifetime=ServiceLifetime.SINGLETON,
            factory=factory,
        )

    def register_transient(
        self,
        service_type: Type[T],
        factory: Callable[["DependencyContainer"], T],
    ) -> None:
        """Register a factory function that produces a new instance on every resolution.

        Args:
            service_type: Type or Interface ABC.
            factory: Callable producing the service.
        """
        self._descriptors[service_type] = _ServiceDescriptor(
            service_type=service_type,
            lifetime=ServiceLifetime.TRANSIENT,
            factory=factory,
        )

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service by its type or interface.

        Args:
            service_type: Target type to resolve.

        Returns:
            Resolved instance of service_type.

        Raises:
            DependencyError: If service is not registered or resolution fails.
        """
        descriptor = self._descriptors.get(service_type)
        if not descriptor:
            raise DependencyError(
                f"No service registered for type '{service_type.__name__}'",
                code=ErrorCode.DEPENDENCY_NOT_FOUND,
                context={"service_type": service_type.__name__},
            )

        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if descriptor.instance is None:
                if not descriptor.factory:
                    raise DependencyError(
                        f"Singleton service '{service_type.__name__}' has no instance or factory",
                        code=ErrorCode.DEPENDENCY_RESOLUTION_FAILED,
                    )
                descriptor.instance = descriptor.factory(self)
            return descriptor.instance

        elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
            if not descriptor.factory:
                raise DependencyError(
                    f"Transient service '{service_type.__name__}' requires a factory",
                    code=ErrorCode.DEPENDENCY_RESOLUTION_FAILED,
                )
            return descriptor.factory(self)

        raise DependencyError(
            f"Unsupported service lifetime for '{service_type.__name__}'",
            code=ErrorCode.DEPENDENCY_RESOLUTION_FAILED,
        )

    def is_registered(self, service_type: Type[Any]) -> bool:
        """Check if a service type is registered in the container."""
        return service_type in self._descriptors

    def clear(self) -> None:
        """Reset container registration state."""
        self._descriptors.clear()
