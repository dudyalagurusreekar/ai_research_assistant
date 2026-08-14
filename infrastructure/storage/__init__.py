"""ARA v1.0 Object Storage package."""

from infrastructure.storage.minio_client import MinIOClientManager, minio_client_manager
from infrastructure.storage.minio_config import MinIOConfig, minio_config
from infrastructure.storage.storage import DiskStorage, IStorage
from infrastructure.storage.storage_manager import ObjectStorageManager, storage_manager

__all__ = [
    "IStorage",
    "DiskStorage",
    "minio_config",
    "MinIOConfig",
    "minio_client_manager",
    "MinIOClientManager",
    "storage_manager",
    "ObjectStorageManager",
]
