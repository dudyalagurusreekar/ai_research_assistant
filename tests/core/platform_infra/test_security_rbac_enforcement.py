"""Security test for Role-Based Access Control (RBAC) and Rate Limiting enforcement."""

import pytest

from core.platform_infra.components.api_gateway import APIGateway
from core.platform_infra.components.auth_manager import AuthManager
from core.platform_infra.models.gateway import APIRequest, APIResponse


def test_security_rbac_and_rate_limiting():
    auth = AuthManager()
    gateway = APIGateway(auth_manager=auth)

    def admin_delete_handler(req: APIRequest) -> APIResponse:
        return APIResponse.success({"deleted": True})

    gateway.register_route(
        "/api/v3/admin/delete", "admin_delete_handler", admin_delete_handler, require_auth=True, required_permission="delete", rate_limit=3
    )

    # 1. Test Viewer Role -> Forbidden (403)
    viewer_token = auth.issue_jwt_token("usr_viewer").access_token
    req_viewer = APIRequest(path="/api/v3/admin/delete", headers={"Authorization": f"Bearer {viewer_token}"})
    res_viewer = gateway.handle_request(req_viewer)
    assert res_viewer.status_code == 403

    # 2. Test Admin Role -> Success (200)
    admin_token = auth.issue_jwt_token("usr_admin").access_token
    req_admin = APIRequest(path="/api/v3/admin/delete", headers={"Authorization": f"Bearer {admin_token}"})
    res_admin1 = gateway.handle_request(req_admin)
    assert res_admin1.status_code == 200

    # 3. Test Rate Limiter -> 429 after 2 requests
    req_admin2 = APIRequest(path="/api/v3/admin/delete", headers={"Authorization": f"Bearer {admin_token}"})
    res_admin2 = gateway.handle_request(req_admin2)
    assert res_admin2.status_code == 200

    req_admin3 = APIRequest(path="/api/v3/admin/delete", headers={"Authorization": f"Bearer {admin_token}"})
    res_admin3 = gateway.handle_request(req_admin3)
    assert res_admin3.status_code == 429
