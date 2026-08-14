"""Cloud Storage Service Connector for S3, GCS, and Azure Blob Storage."""

from typing import Dict, Any, Optional, List
import time

from tools.integration.sdk.storage_connector_base import StorageConnector


class CloudStorageServiceConnector(StorageConnector):
    """Universal Connector for Object Storage (S3, GCS, Azure Blob)."""

    def __init__(
        self,
        name: str = "cloud_storage",
        provider: str = "s3",
        default_bucket: str = "ara-research-bucket",
    ) -> None:
        super().__init__(
            name=name,
            provider=provider,
            default_bucket=default_bucket,
            description="Cloud Storage service connector for buckets, objects, and presigned URLs",
        )
        self._mock_objects: Dict[str, Dict[str, Dict[str, Any]]] = {
            self._default_bucket: {
                "datasets/raw_data.csv": {
                    "key": "datasets/raw_data.csv",
                    "size": 10240,
                    "last_modified": "2026-08-01T10:00:00Z",
                    "content": "id,val\n1,100\n2,200\n",
                    "content_type": "text/csv",
                },
                "reports/summary_v1.pdf": {
                    "key": "reports/summary_v1.pdf",
                    "size": 54000,
                    "last_modified": "2026-08-01T12:00:00Z",
                    "content": "PDF report content",
                    "content_type": "application/pdf",
                },
            }
        }

    async def list_objects(self, bucket: str = "", prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List objects in bucket filtered by prefix."""
        target_bucket = bucket or self._default_bucket
        b_store = self._mock_objects.get(target_bucket, {})

        results = []
        for key, obj in b_store.items():
            if not prefix or key.startswith(prefix):
                results.append({"key": obj["key"], "size": obj["size"], "last_modified": obj["last_modified"]})

        return results[:limit]

    async def get_object(self, bucket: str, key: str) -> Dict[str, Any]:
        """Fetch object content and metadata."""
        target_bucket = bucket or self._default_bucket
        b_store = self._mock_objects.get(target_bucket, {})
        obj = b_store.get(key)
        if obj:
            return obj
        raise ValueError(f"Object '{key}' not found in bucket '{target_bucket}'.")

    async def put_object(self, bucket: str, key: str, content: Any, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        """Upload object into storage bucket."""
        target_bucket = bucket or self._default_bucket
        if target_bucket not in self._mock_objects:
            self._mock_objects[target_bucket] = {}

        obj = {
            "key": key,
            "size": len(str(content)),
            "last_modified": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content": content,
            "content_type": content_type,
        }
        self._mock_objects[target_bucket][key] = obj
        return {"status": "uploaded", "bucket": target_bucket, "key": key, "size": obj["size"]}

    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete object from storage bucket."""
        target_bucket = bucket or self._default_bucket
        b_store = self._mock_objects.get(target_bucket, {})
        if key in b_store:
            del b_store[key]
            return True
        return False

    async def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600, method: str = "GET") -> str:
        """Generate presigned download or upload URL."""
        target_bucket = bucket or self._default_bucket
        return f"https://{target_bucket}.s3.amazonaws.com/{key}?Signature=presigned_token_123&Expires={int(time.time()) + expires_in}"
