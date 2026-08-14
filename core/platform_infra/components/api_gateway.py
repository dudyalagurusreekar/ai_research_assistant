"""API Gateway — Unified routing, rate limiting, authentication middleware, and CORS header management."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from core.platform_infra.components.auth_manager import AuthManager
from core.platform_infra.models.gateway import APIRequest, APIResponse, RateLimitPolicy, RouteConfig
from utils.logger import get_logger

logger = get_logger("APIGateway")


class APIGateway:
    """Unified API Gateway for request dispatching, security enforcement, and rate limiting."""

    def __init__(self, auth_manager: Optional[AuthManager] = None) -> None:
        self.auth_manager = auth_manager or AuthManager()
        self._routes: Dict[str, RouteConfig] = {}
        self._handlers: Dict[str, Callable[[APIRequest], APIResponse]] = {}
        self._rate_counters: Dict[str, List[float]] = {}  # ip -> timestamps

    def register_route(
        self,
        path: str,
        handler_name: str,
        handler_func: Callable[[APIRequest], APIResponse],
        require_auth: bool = True,
        required_permission: str = "read",
        rate_limit: int = 120,
    ) -> None:
        """Register path route with security policies and target handler."""
        policy = RateLimitPolicy(max_requests_per_minute=rate_limit)
        config = RouteConfig(
            path_pattern=path,
            target_handler=handler_name,
            require_auth=require_auth,
            required_permission=required_permission,
            rate_limit_policy=policy,
        )
        self._routes[path] = config
        self._handlers[handler_name] = handler_func
        logger.info(f"APIGateway registered route '{path}' -> '{handler_name}' [AuthRequired: {require_auth}]")

    def handle_request(self, request: APIRequest) -> APIResponse:
        """Process inbound APIRequest through security middleware, rate limiters, and target route handlers."""
        start_t = time.time()
        logger.info(f"APIGateway [{request.request_id}] Inbound Request: {request.method} {request.path}")

        # 1. Route Lookup
        route = self._routes.get(request.path)
        if not route:
            return APIResponse.error(f"Route '{request.path}' not found.", status_code=404, request_id=request.request_id)

        # 2. Rate Limiting Check
        if not self._check_rate_limit(request.client_ip, route.rate_limit_policy):
            return APIResponse.error("Rate limit exceeded. Please try again later.", status_code=429, request_id=request.request_id)

        # 3. Authentication & Authorization Middleware
        if route.require_auth:
            token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
            api_key = request.headers.get("X-API-Key", "").strip()

            auth_ctx = None
            if token:
                try:
                    auth_ctx = self.auth_manager.verify_jwt_token(token)
                except Exception as exc:
                    return APIResponse.error(f"Authentication failed: {exc}", status_code=401, request_id=request.request_id)
            elif api_key:
                try:
                    auth_ctx = self.auth_manager.verify_api_key(api_key)
                except Exception as exc:
                    return APIResponse.error(f"Invalid API Key: {exc}", status_code=401, request_id=request.request_id)
            else:
                return APIResponse.error("Missing Authorization Header or X-API-Key.", status_code=401, request_id=request.request_id)

            # RBAC Permission Check
            if not self.auth_manager.check_rbac(auth_ctx, route.required_permission):
                return APIResponse.error(
                    f"Forbidden: Identity lacks required permission '{route.required_permission}'.",
                    status_code=403,
                    request_id=request.request_id,
                )

        # 4. Target Handler Execution
        handler = self._handlers.get(route.target_handler)
        if not handler:
            return APIResponse.error("Handler function unavailable.", status_code=500, request_id=request.request_id)

        try:
            response = handler(request)
            response.request_id = request.request_id
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["X-Response-Time-Ms"] = f"{(time.time() - start_t) * 1000.0:.2f}"
            return response
        except Exception as exc:
            logger.exception(f"APIGateway Handler Exception: {exc}")
            return APIResponse.error(f"Internal Gateway Error: {exc}", status_code=500, request_id=request.request_id)

    def _check_rate_limit(self, client_ip: str, policy: RateLimitPolicy) -> bool:
        """Sliding window rate limit check."""
        now = time.time()
        window_start = now - 60.0

        if client_ip not in self._rate_counters:
            self._rate_counters[client_ip] = []

        self._rate_counters[client_ip] = [t for t in self._rate_counters[client_ip] if t >= window_start]

        if len(self._rate_counters[client_ip]) >= policy.max_requests_per_minute:
            return False

        self._rate_counters[client_ip].append(now)
        return True
