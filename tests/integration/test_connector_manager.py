"""Unit tests for ConnectorManager, registry, dynamic loading, and circuit breaking."""

import pytest
import asyncio

from tools.integration.manager.connector_manager import ConnectorManager, CircuitBreaker
from tools.integration.connectors.gmail_connector import GmailConnector
from tools.integration.connectors.github_connector import GitHubConnector
from tools.integration.models.integration_models import IntegrationRequest


def test_connector_manager_registry_and_execution():
    async def _test():
        mgr = ConnectorManager()
        gmail = GmailConnector()
        github = GitHubConnector()

        mgr.register_connector(gmail)
        mgr.register_connector(github)

        assert len(mgr.list_connectors()) == 2
        assert mgr.get_connector("gmail") is not None
        assert mgr.get_connector("github") is not None

        req = IntegrationRequest(connector_name="gmail", method="SEARCH", params={"q": "Research"})
        res = await mgr.execute_request(req)
        assert res.success is True
        assert res.status_code == 200
        assert "messages" in res.data

    asyncio.run(_test())


def test_circuit_breaker_failure_threshold():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
    assert cb.can_execute() is True

    cb.record_failure()
    cb.record_failure()
    assert cb.can_execute() is True

    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False
