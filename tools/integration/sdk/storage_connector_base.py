"""StorageConnector base class for cloud object storage integrations (S3, GCS, Azure Blob)."""

from abc import abstractmethod
from typing import Dict, Any, Optional, List

from tools.integration.sdk.base_connector import BaseConnector
from tools.integration.models.integration_models import (
    ProtocolType,
    IntegrationRequest,
    IntegrationResponse,
)


class StorageConnector(BaseConnector):
    """Specialized BaseConnector for object storage capabilities."""

    def __init__(
        self,
        name: str = "cloud_storage",
        provider: str = "s3",
        default_bucket: str = "ara-storage",
        description: str = "Cloud Storage connector for buckets and objects",
    ) -> None:
        super().__init__(name=name, protocol=ProtocolType.REST, base_url="", description=description)
        self._provider = provider
        self._default_bucket = default_bucket

    @abstractmethod
    async def list_objects(self, bucket: str = "", prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List objects in target storage bucket."""
        pass

    @abstractmethod
    async def get_object(self, bucket: str, key: str) -> Dict[str, Any]:
        """Fetch object content and metadata."""
        pass

    @abstractmethod
    async def put_object(self, bucket: str, key: str, content: Any, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        """Upload object to storage bucket."""
        pass

    @abstractmethod
    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete object from storage bucket."""
        pass

    @abstractmethod
    async def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600, method: str = "GET") -> str:
        """Generate presigned download or upload URL."""
        pass

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Dispatch storage request based on request method."""
        method = request.method.upper()
        bucket = request.params.get("bucket", self._default_bucket)
        key = request.params.get("key", request.endpoint_or_tool)

        if method in ["LIST", "LIST_OBJECTS"]:
            prefix = request.params.get("prefix", "")
            limit = request.params.get("limit", 100)
            objects = await self.list_objects(bucket=bucket, prefix=prefix, limit=limit)
            return IntegrationResponse(status_code=200, data={"bucket": bucket, "objects": objects})

        elif method in ["GET", "GET_OBJECT", "DOWNLOAD"]:
            obj_data = await self.get_object(bucket=bucket, key=key)
            return IntegrationResponse(status_code=200, data=obj_data)

        elif method in ["PUT", "PUT_OBJECT", "UPLOAD", "POST"]:
            content = request.body or request.params.get("content", "")
            content_type = request.params.get("content_type", "text/plain")
            res = await self.put_object(bucket=bucket, key=key, content=content, content_type=content_type)
            return IntegrationResponse(status_code=200, data=res)

        elif method in ["DELETE", "DELETE_OBJECT"]:
            deleted = await self.delete_object(bucket=bucket, key=key)
            return IntegrationResponse(status_code=200, data={"deleted": deleted, "key": key})

        elif method in ["PRESIGNED_URL"]:
            expires_in = request.params.get("expires_in", 3600)
            url = await self.generate_presigned_url(bucket=bucket, key=key, expires_in=expires_in)
            return IntegrationResponse(status_code=200, data={"presigned_url": url, "expires_in": expires_in})

        return IntegrationResponse(status_code=400, error_message=f"Unsupported storage action '{method}'")
