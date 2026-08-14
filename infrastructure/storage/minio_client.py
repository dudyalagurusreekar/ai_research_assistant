"""MinIO Object Storage Client Manager with fallback local storage for test isolation."""

import hashlib
import io
import os
from datetime import timedelta
from pathlib import Path
from typing import Optional
from infrastructure.storage.minio_config import minio_config
from utils.logger import get_logger

logger = get_logger("MinIOClientManager")

try:
    from minio import Minio
    HAS_MINIO = True
except ImportError:
    Minio = None
    HAS_MINIO = False


class LocalStorageFallback:
    """Mock MinIO object store using local disk directory (.storage/) for unit test isolation."""

    def __init__(self, base_dir: str = ".storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def bucket_exists(self, bucket_name: str) -> bool:
        return (self.base_dir / bucket_name).exists()

    def make_bucket(self, bucket_name: str) -> None:
        (self.base_dir / bucket_name).mkdir(parents=True, exist_ok=True)

    def put_object(self, bucket_name: str, object_name: str, data: io.BytesIO, length: int, content_type: str = "application/octet-stream") -> None:
        target_path = self.base_dir / bucket_name / object_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(data.read())

    def get_object(self, bucket_name: str, object_name: str):
        target_path = self.base_dir / bucket_name / object_name
        if not target_path.exists():
            raise FileNotFoundError(f"Object {object_name} not found in bucket {bucket_name}")
        with open(target_path, "rb") as f:
            content = f.read()
        
        # Return response wrapper matching minio get_object
        class ObjectResponse:
            def __init__(self, data_bytes):
                self._data = data_bytes
            def read(self):
                return self._data
            def close(self):
                pass
            def release_conn(self):
                pass

        return ObjectResponse(content)

    def remove_object(self, bucket_name: str, object_name: str) -> None:
        target_path = self.base_dir / bucket_name / object_name
        if target_path.exists():
            target_path.unlink()

    def presigned_get_object(self, bucket_name: str, object_name: str, expires: timedelta) -> str:
        return f"file://{(self.base_dir / bucket_name / object_name).absolute()}"


class MinIOClientManager:
    """Production MinIO manager with automatic bucket initialization and fallback handling."""

    def __init__(self):
        self._client = None
        self._is_fallback = False
        self._connect()

    def _connect(self) -> None:
        if HAS_MINIO and Minio is not None:
            try:
                client = Minio(
                    endpoint=minio_config.endpoint,
                    access_key=minio_config.access_key,
                    secret_key=minio_config.secret_key,
                    secure=minio_config.secure,
                )
                # Test connectivity
                client.list_buckets()
                self._client = client
                self._is_fallback = False
                logger.info(f"Connected to MinIO at {minio_config.endpoint}")
                self.ensure_buckets_exist()
                return
            except Exception as exc:
                logger.warning(f"Could not connect to MinIO server ({exc}). Initializing local storage fallback.")

        self._client = LocalStorageFallback()
        self._is_fallback = True
        self.ensure_buckets_exist()

    @property
    def is_fallback(self) -> bool:
        return self._is_fallback

    def ensure_buckets_exist(self) -> None:
        """Create all dedicated ARA buckets if they do not already exist."""
        for b_name in minio_config.buckets:
            try:
                if not self._client.bucket_exists(b_name):
                    self._client.make_bucket(b_name)
                    logger.info(f"Created MinIO bucket: {b_name}")
            except Exception as exc:
                logger.error(f"Error creating bucket {b_name}: {exc}")

    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to a MinIO bucket and return object reference path."""
        data_stream = io.BytesIO(data)
        data_len = len(data)
        
        self._client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=data_stream,
            length=data_len,
            content_type=content_type,
        )
        return f"{bucket_name}/{object_name}"

    def download_bytes(self, bucket_name: str, object_name: str) -> bytes:
        """Download object content as raw bytes."""
        response = self._client.get_object(bucket_name, object_name)
        try:
            return response.read()
        finally:
            if hasattr(response, "close"):
                response.close()
            if hasattr(response, "release_conn"):
                response.release_conn()

    def get_presigned_url(self, bucket_name: str, object_name: str, expires_seconds: int = 3600) -> str:
        """Generate presigned GET URL for object download."""
        return self._client.presigned_get_object(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=timedelta(seconds=expires_seconds),
        )

    def delete_object(self, bucket_name: str, object_name: str) -> None:
        """Remove object from bucket."""
        self._client.remove_object(bucket_name, object_name)

    @staticmethod
    def calculate_sha256(data: bytes) -> str:
        """Calculate hex SHA256 digest for object integrity verification."""
        return hashlib.sha256(data).hexdigest()


# Global MinIO Client Manager instance
minio_client_manager = MinIOClientManager()
