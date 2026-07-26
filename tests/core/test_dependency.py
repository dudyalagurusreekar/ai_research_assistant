"""Unit tests for Dependency Injection Container."""

import unittest
from abc import ABC, abstractmethod
from core.dependency import DependencyContainer
from core.exceptions import DependencyError


class IDummyService(ABC):
    @abstractmethod
    def getValue(self) -> str:
        pass


class DummyService(IDummyService):
    def __init__(self, val: str = "default") -> None:
        self.val = val

    def getValue(self) -> str:
        return self.val


class TestDependencyContainer(unittest.TestCase):
    """Test IoC dependency registration and resolution."""

    def test_register_instance(self):
        container = DependencyContainer()
        svc = DummyService("instance_value")
        container.register_instance(IDummyService, svc)

        resolved = container.resolve(IDummyService)
        self.assertIs(resolved, svc)
        self.assertEqual(resolved.getValue(), "instance_value")

    def test_register_singleton_factory(self):
        container = DependencyContainer()
        container.register_singleton(IDummyService, lambda c: DummyService("singleton"))

        res1 = container.resolve(IDummyService)
        res2 = container.resolve(IDummyService)
        self.assertIs(res1, res2)
        self.assertEqual(res1.getValue(), "singleton")

    def test_register_transient(self):
        container = DependencyContainer()
        container.register_transient(IDummyService, lambda c: DummyService("transient"))

        res1 = container.resolve(IDummyService)
        res2 = container.resolve(IDummyService)
        self.assertIsNot(res1, res2)

    def test_unregistered_service_raises(self):
        container = DependencyContainer()
        with self.assertRaises(DependencyError):
            container.resolve(IDummyService)


if __name__ == "__main__":
    unittest.main()
