"""Storage infrastructure package."""

from infrastructure.storage.storage import IStorage, DiskStorage

__all__ = [
    "IStorage",
    "DiskStorage",
]
