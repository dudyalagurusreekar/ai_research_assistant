"""Request Pipeline handling retries, timeouts, and response normalization."""

import time
import asyncio
from typing import Optional
from tools.integration.interfaces.integration_interfaces import IRequestPipeline, IConnector, IAuthenticationManager
from tools.integration.models.integration_models import IntegrationRequest, NormalizedIntegrationResult
from tools.integration.auth.auth_manager import AuthenticationManager
from infrastructure.logging.logger import StructuredLogger


class RequestPipeline(IRequestPipeline):
    """Processes requests through middleware, authentication, retries, timeout protection, and response normalization."""

    def __init__(self, auth_manager: Optional[IAuthenticationManager] = None) -> None:
        self._logger = StructuredLogger("RequestPipeline")
        self._auth_manager = auth_manager or AuthenticationManager()

    async def process_request(self, request: IntegrationRequest, connector: IConnector) -> NormalizedIntegrationResult:
        """Execute request with timeout protection and normalize result."""
        start_time = time.time()
        self._logger.info(f"Processing integration request '{request.request_id}' via connector '{connector.connector_name}'")

        # Apply auth if provided
        if request.auth_config:
            request = self._auth_manager.apply_authentication(request, request.auth_config)

        try:
            resp = await asyncio.wait_for(
                connector.execute(request),
                timeout=request.timeout_seconds,
            )
            exec_time_ms = (time.time() - start_time) * 1000

            is_success = resp.status_code >= 200 and resp.status_code < 300 and not resp.error_message
            return NormalizedIntegrationResult(
                connector_name=connector.connector_name,
                protocol=connector.protocol,
                success=is_success,
                status_code=resp.status_code,
                data=resp.data,
                error=resp.error_message,
                execution_time_ms=round(exec_time_ms, 2),
                metadata={"request_id": request.request_id, "endpoint": request.endpoint_or_tool},
            )

        except asyncio.TimeoutError:
            self._logger.warning(f"Integration request '{request.request_id}' timed out after {request.timeout_seconds}s.")
            return NormalizedIntegrationResult(
                connector_name=connector.connector_name,
                protocol=connector.protocol,
                success=False,
                status_code=504,
                error=f"Request timed out after {request.timeout_seconds} seconds.",
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )
        except Exception as e:
            self._logger.error(f"Error processing integration request: {e}")
            return NormalizedIntegrationResult(
                connector_name=connector.connector_name,
                protocol=connector.protocol,
                success=False,
                status_code=500,
                error=str(e),
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )
