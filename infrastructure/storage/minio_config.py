"""MinIO Object Storage Configuration provider."""

from typing import List
from config.settings import settings


class MinIOConfig:
    """MinIO storage connection and bucket options."""

    @property
    def endpoint(self) -> str:
        return settings.MINIO_ENDPOINT

    @property
    def access_key(self) -> str:
        return settings.MINIO_ACCESS_KEY

    @property
    def secret_key(self) -> str:
        return settings.MINIO_SECRET_KEY

    @property
    def secure(self) -> bool:
        return settings.MINIO_SECURE

    @property
    def buckets(self) -> List[str]:
        return [
            settings.MINIO_BUCKET_UPLOADS,
            settings.MINIO_BUCKET_REPORTS,
            settings.MINIO_BUCKET_DATASETS,
            settings.MINIO_BUCKET_SCREENSHOTS,
            settings.MINIO_BUCKET_BROWSER_DOWNLOADS,
            settings.MINIO_BUCKET_BROWSER_UPLOADS,
            settings.MINIO_BUCKET_GENERATED_FILES,
            settings.MINIO_BUCKET_TEMP_ASSETS,
        ]


minio_config = MinIOConfig()
