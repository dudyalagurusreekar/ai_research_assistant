"""Dependency Injection package for the Core Foundation."""

from core.dependency.container import DependencyContainer, ServiceLifetime

__all__ = [
    "DependencyContainer",
    "ServiceLifetime",
]
