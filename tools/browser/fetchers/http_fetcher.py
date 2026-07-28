"""Concrete HTTP Network Fetcher Strategy for the Browser Tool.

This module implements `HTTPFetcher`, a production-grade, highly reliable
HTTP/HTTPS network client built on top of `httpx`. It provides connection pooling,
URL normalization, header management, configurable timeouts, SSL verification,
redirect tracking, response payload size capping, MIME type detection, exponential
backoff retries, and comprehensive error mapping using custom Browser Tool exceptions.
"""

import asyncio
import random
import time
from typing import Dict, Optional, Tuple
import httpx

from tools.browser.config import BrowserConfig
from tools.browser.constants import HttpMethod
from tools.browser.core.base_fetcher import BaseFetcher
from tools.browser.exceptions import (
    FetchError,
    TimeoutError,
    NetworkError,
)
from tools.browser.models.request import NavigationParams
from tools.browser.models.response import FetchResult
from tools.browser.utils.helpers import sanitize_url, validate_url
from tools.browser.utils.logging import get_browser_logger

# Status codes considered transient and eligible for exponential backoff retries
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class HTTPFetcher(BaseFetcher):
    """Production-ready HTTP network fetcher powered by `httpx`.

    Inherits from `BaseFetcher` (Strategy Pattern), supporting synchronous
    and asynchronous resource retrieval with connection pooling, retries,
    content capping, and custom exception translation.

    Attributes:
        config (BrowserConfig): Reference to browser configuration settings.
    """

    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        """Initialize HTTPFetcher with configuration and connection pools.

        Args:
            config (Optional[BrowserConfig]): Browser configuration settings.
        """
        cfg = config or BrowserConfig()
        cfg.validate()
        super().__init__(cfg)

        self._logger = get_browser_logger("HTTPFetcher")
        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.Client:
        """Get or lazily initialize the shared synchronous `httpx.Client`."""
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            timeout = httpx.Timeout(self.config.timeout_seconds)
            self._client = httpx.Client(
                follow_redirects=self.config.follow_redirects,
                max_redirects=self.config.max_redirects,
                verify=self.config.verify_ssl,
                timeout=timeout,
                limits=limits,
                headers=self._build_default_headers(),
            )
        return self._client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or lazily initialize the shared asynchronous `httpx.AsyncClient`."""
        if self._async_client is None or self._async_client.is_closed:
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            timeout = httpx.Timeout(self.config.timeout_seconds)
            self._async_client = httpx.AsyncClient(
                follow_redirects=self.config.follow_redirects,
                max_redirects=self.config.max_redirects,
                verify=self.config.verify_ssl,
                timeout=timeout,
                limits=limits,
                headers=self._build_default_headers(),
            )
        return self._async_client

    def _build_default_headers(self) -> Dict[str, str]:
        """Construct normalized default HTTP headers combining User-Agent."""
        headers = dict(self.config.default_headers)
        if "User-Agent" not in headers and "user-agent" not in headers:
            headers["User-Agent"] = self.config.user_agent
        return headers

    def _prepare_request_headers(self, custom_headers: Dict[str, str]) -> Dict[str, str]:
        """Merge base default headers with request-specific headers.

        Args:
            custom_headers (Dict[str, str]): Per-request header overrides.

        Returns:
            Dict[str, str]: Combined headers dictionary.
        """
        headers = self._build_default_headers()
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def _parse_content_type(self, headers: httpx.Headers) -> Tuple[str, str]:
        """Extract MIME type and charset encoding from HTTP response headers.

        Args:
            headers (httpx.Headers): Response HTTP headers.

        Returns:
            Tuple[str, str]: (mime_type, encoding) pair.
        """
        content_type_header = headers.get("content-type", "text/html; charset=utf-8")
        parts = [p.strip() for p in content_type_header.split(";")]
        mime_type = parts[0].lower() if parts else "text/html"

        encoding = "utf-8"
        for part in parts[1:]:
            if part.lower().startswith("charset="):
                encoding = part.split("=", 1)[1].strip('\'"').lower()
                break

        return mime_type, encoding

    def _validate_content_length(self, headers: httpx.Headers, url: str) -> None:
        """Check Content-Length header against max allowed page size.

        Args:
            headers (httpx.Headers): HTTP response headers.
            url (str): Target URL string.

        Raises:
            FetchError: If Content-Length exceeds max_page_size_bytes limit.
        """
        content_length_str = headers.get("content-length")
        if content_length_str and content_length_str.isdigit():
            content_length = int(content_length_str)
            if content_length > self.config.max_page_size_bytes:
                raise FetchError(
                    f"Response size ({content_length} bytes) exceeds maximum payload limit "
                    f"({self.config.max_page_size_bytes} bytes)",
                    url=url,
                )

    def fetch(self, params: NavigationParams) -> FetchResult:
        """Fetch a web resource synchronously given navigation parameters.

        Args:
            params (NavigationParams): Navigation request parameters.

        Returns:
            FetchResult: Raw network response result with metadata.

        Raises:
            ValidationError: If URL parameter is invalid.
            TimeoutError: If request exceeds specified timeout limit.
            NetworkError: If underlying socket/DNS network error occurs.
            FetchError: If max payload size or redirect limit is violated.
        """
        # 1. URL Validation & Sanitization
        sanitized_url = sanitize_url(params.url)
        validate_url(sanitized_url)

        headers = self._prepare_request_headers(params.headers)
        method = params.method.value if isinstance(params.method, HttpMethod) else str(params.method)
        timeout_val = params.timeout or self.config.timeout_seconds
        httpx_timeout = httpx.Timeout(timeout_val)

        client = self._get_client()
        attempts = 0
        max_retries = max(1, self.config.max_retries)

        start_time = time.time()
        last_exception: Optional[Exception] = None

        while attempts < max_retries:
            attempts += 1
            try:
                self._logger.debug(f"HTTP fetch attempt {attempts}/{max_retries} for URL '{sanitized_url}'")
                
                # Stream response to validate payload size dynamically
                with client.stream(
                    method=method,
                    url=sanitized_url,
                    headers=headers,
                    timeout=httpx_timeout,
                    follow_redirects=self.config.follow_redirects,
                ) as response:
                    # Check Content-Length header early
                    self._validate_content_length(response.headers, sanitized_url)

                    # Check transient HTTP error status for retry eligibility
                    if response.status_code in RETRYABLE_STATUS_CODES and attempts < max_retries:
                        backoff = self.config.backoff_factor * (2 ** (attempts - 1)) + random.uniform(0, 0.1)
                        self._logger.warning(
                            f"HTTP {response.status_code} received from '{sanitized_url}'. "
                            f"Retrying in {backoff:.2f}s (Attempt {attempts}/{max_retries})"
                        )
                        time.sleep(backoff)
                        continue

                    # Read streamed content chunks while verifying size limit
                    content_chunks = []
                    total_bytes = 0
                    for chunk in response.iter_bytes(chunk_size=65536):
                        total_bytes += len(chunk)
                        if total_bytes > self.config.max_page_size_bytes:
                            raise FetchError(
                                f"Response payload exceeded maximum size limit "
                                f"({self.config.max_page_size_bytes} bytes) during download",
                                url=sanitized_url,
                            )
                        content_chunks.append(chunk)

                    raw_content = b"".join(content_chunks)
                    response_time = (time.time() - start_time) * 1000.0

                    mime_type, header_encoding = self._parse_content_type(response.headers)
                    detected_encoding = response.encoding or header_encoding or "utf-8"
                    redirect_count = len(response.history)
                    final_url = str(response.url)

                    is_success = 200 <= response.status_code < 400
                    error_msg = None if is_success else f"HTTP Status {response.status_code}"

                    return FetchResult(
                        url=final_url,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        content=raw_content,
                        encoding=detected_encoding,
                        mime_type=mime_type,
                        redirect_count=redirect_count,
                        response_time_ms=response_time,
                        success=is_success,
                        error_message=error_msg,
                    )

            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"Network request timed out: {e}", url=sanitized_url)
            except (httpx.NetworkError, httpx.ProtocolError) as e:
                last_exception = NetworkError(f"Network socket failure: {e}", url=sanitized_url)
            except httpx.TooManyRedirects as e:
                raise FetchError(f"Exceeded maximum redirects threshold: {e}", url=sanitized_url)
            except FetchError:
                raise
            except httpx.RequestError as e:
                last_exception = NetworkError(f"HTTP request error: {e}", url=sanitized_url)
            except Exception as e:
                last_exception = FetchError(f"Unexpected network error during fetch: {e}", url=sanitized_url)

            if attempts < max_retries:
                backoff = self.config.backoff_factor * (2 ** (attempts - 1)) + random.uniform(0, 0.1)
                self._logger.warning(
                    f"Transient network error for '{sanitized_url}': {last_exception}. "
                    f"Retrying in {backoff:.2f}s (Attempt {attempts}/{max_retries})"
                )
                time.sleep(backoff)

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise FetchError(f"Failed to fetch resource from '{sanitized_url}' after {max_retries} attempts.", url=sanitized_url)

    async def fetch_async(self, params: NavigationParams) -> FetchResult:
        """Fetch a web resource asynchronously given navigation parameters.

        Args:
            params (NavigationParams): Navigation request parameters.

        Returns:
            FetchResult: Raw network response result with metadata.

        Raises:
            ValidationError: If URL parameter is invalid.
            TimeoutError: If request exceeds specified timeout limit.
            NetworkError: If underlying socket/DNS network error occurs.
            FetchError: If max payload size or redirect limit is violated.
        """
        sanitized_url = sanitize_url(params.url)
        validate_url(sanitized_url)

        headers = self._prepare_request_headers(params.headers)
        method = params.method.value if isinstance(params.method, HttpMethod) else str(params.method)
        timeout_val = params.timeout or self.config.timeout_seconds
        httpx_timeout = httpx.Timeout(timeout_val)

        client = self._get_async_client()
        attempts = 0
        max_retries = max(1, self.config.max_retries)

        start_time = time.time()
        last_exception: Optional[Exception] = None

        while attempts < max_retries:
            attempts += 1
            try:
                self._logger.debug(f"[Async] HTTP fetch attempt {attempts}/{max_retries} for URL '{sanitized_url}'")

                async with client.stream(
                    method=method,
                    url=sanitized_url,
                    headers=headers,
                    timeout=httpx_timeout,
                    follow_redirects=self.config.follow_redirects,
                ) as response:
                    self._validate_content_length(response.headers, sanitized_url)

                    if response.status_code in RETRYABLE_STATUS_CODES and attempts < max_retries:
                        backoff = self.config.backoff_factor * (2 ** (attempts - 1)) + random.uniform(0, 0.1)
                        self._logger.warning(
                            f"[Async] HTTP {response.status_code} received from '{sanitized_url}'. "
                            f"Retrying in {backoff:.2f}s (Attempt {attempts}/{max_retries})"
                        )
                        await asyncio.sleep(backoff)
                        continue

                    content_chunks = []
                    total_bytes = 0
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        total_bytes += len(chunk)
                        if total_bytes > self.config.max_page_size_bytes:
                            raise FetchError(
                                f"Response payload exceeded maximum size limit "
                                f"({self.config.max_page_size_bytes} bytes) during download",
                                url=sanitized_url,
                            )
                        content_chunks.append(chunk)

                    raw_content = b"".join(content_chunks)
                    response_time = (time.time() - start_time) * 1000.0

                    mime_type, header_encoding = self._parse_content_type(response.headers)
                    detected_encoding = response.encoding or header_encoding or "utf-8"
                    redirect_count = len(response.history)
                    final_url = str(response.url)

                    is_success = 200 <= response.status_code < 400
                    error_msg = None if is_success else f"HTTP Status {response.status_code}"

                    return FetchResult(
                        url=final_url,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        content=raw_content,
                        encoding=detected_encoding,
                        mime_type=mime_type,
                        redirect_count=redirect_count,
                        response_time_ms=response_time,
                        success=is_success,
                        error_message=error_msg,
                    )

            except httpx.TimeoutException as e:
                last_exception = TimeoutError(f"Network request timed out: {e}", url=sanitized_url)
            except (httpx.NetworkError, httpx.ProtocolError) as e:
                last_exception = NetworkError(f"Network socket failure: {e}", url=sanitized_url)
            except httpx.TooManyRedirects as e:
                raise FetchError(f"Exceeded maximum redirects threshold: {e}", url=sanitized_url)
            except FetchError:
                raise
            except httpx.RequestError as e:
                last_exception = NetworkError(f"HTTP request error: {e}", url=sanitized_url)
            except Exception as e:
                last_exception = FetchError(f"Unexpected network error during fetch: {e}", url=sanitized_url)

            if attempts < max_retries:
                backoff = self.config.backoff_factor * (2 ** (attempts - 1)) + random.uniform(0, 0.1)
                self._logger.warning(
                    f"[Async] Transient network error for '{sanitized_url}': {last_exception}. "
                    f"Retrying in {backoff:.2f}s (Attempt {attempts}/{max_retries})"
                )
                await asyncio.sleep(backoff)

        if last_exception:
            raise last_exception
        raise FetchError(f"Failed to fetch resource from '{sanitized_url}' after {max_retries} attempts.", url=sanitized_url)

    def close(self) -> None:
        """Close synchronous client and release connection pool resources."""
        if self._client and not self._client.is_closed:
            self._logger.info("Closing HTTPFetcher synchronous connection pool.")
            self._client.close()
            self._client = None

    async def aclose(self) -> None:
        """Close asynchronous client and release connection pool resources."""
        if self._async_client and not self._async_client.is_closed:
            self._logger.info("Closing HTTPFetcher asynchronous connection pool.")
            await self._async_client.aclose()
            self._async_client = None

    def __enter__(self) -> "HTTPFetcher":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    async def __aenter__(self) -> "HTTPFetcher":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
