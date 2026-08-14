"""Unit test for APIGateway."""

import pytest

from core.platform_infra.components.api_gateway import APIGateway
from core.platform_infra.components.auth_manager import AuthManager
from core.platform_infra.models.gateway import APIRequest, APIResponse


def test_api_gateway_routing_and_auth():
    auth_manager = AuthManager()
    gateway = APIGateway(auth_manager=auth_manager)

    def dummy_handler(req: APIRequest) -> APIResponse:
        return APIResponse.success({"message": "Hello ARA Platform"})

    gateway.register_route("/api/v3/research", "dummy_handler", dummy_handler, require_auth=True, required_permission="read")

    # Request without token -> 401
    req_unauth = APIRequest(path="/api/v3/research")
    res_unauth = gateway.handle_request(req_unauth)
    assert res_unauth.status_code == 401

    # Request with token -> 200
    token = auth_manager.issue_jwt_token("usr_admin").access_token
    req_auth = APIRequest(path="/api/v3/research", headers={"Authorization": f"Bearer {token}"})
    res_auth = gateway.handle_request(req_auth)
    assert res_auth.status_code == 200
    assert res_auth.data.get("message") == "Hello ARA Platform"
