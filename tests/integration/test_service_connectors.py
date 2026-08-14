"""Unit tests for all 9 Sprint 12 Service Connectors."""

import pytest
import asyncio

from tools.integration.connectors.gmail_connector import GmailConnector
from tools.integration.connectors.google_drive_connector import GoogleDriveConnector
from tools.integration.connectors.github_connector import GitHubConnector
from tools.integration.connectors.slack_connector import SlackConnector
from tools.integration.connectors.jira_connector import JiraConnector
from tools.integration.connectors.notion_connector import NotionConnector
from tools.integration.connectors.calendar_connector import CalendarConnector
from tools.integration.connectors.database_connector import DatabaseServiceConnector
from tools.integration.connectors.cloud_storage_connector import CloudStorageServiceConnector

from tools.integration.models.integration_models import IntegrationRequest


def test_gmail_connector():
    async def _test():
        c = GmailConnector()
        await c.initialize()

        req_search = IntegrationRequest(method="SEARCH", params={"q": "Research"})
        res_search = await c.execute(req_search)
        assert res_search.status_code == 200
        assert len(res_search.data["messages"]) >= 1

        req_send = IntegrationRequest(method="SEND", params={"to": "test@example.com", "subject": "Test", "body": "Body"})
        res_send = await c.execute(req_send)
        assert res_send.status_code == 201
        assert res_send.data["status"] == "sent"

    asyncio.run(_test())


def test_google_drive_connector():
    async def _test():
        c = GoogleDriveConnector()
        req = IntegrationRequest(method="LIST_FILES")
        res = await c.execute(req)
        assert res.status_code == 200
        assert len(res.data["files"]) >= 1

    asyncio.run(_test())


def test_github_connector():
    async def _test():
        c = GitHubConnector()
        req = IntegrationRequest(method="SEARCH_ISSUES", params={"query": "Universal"})
        res = await c.execute(req)
        assert res.status_code == 200
        assert len(res.data["issues"]) >= 1

    asyncio.run(_test())


def test_slack_connector():
    async def _test():
        c = SlackConnector()
        req = IntegrationRequest(method="POST_MESSAGE", params={"channel": "general", "text": "Hello Slack"})
        res = await c.execute(req)
        assert res.status_code == 200
        assert res.data["ok"] is True

    asyncio.run(_test())


def test_jira_connector():
    async def _test():
        c = JiraConnector()
        req = IntegrationRequest(method="SEARCH_JQL", params={"q": "Universal"})
        res = await c.execute(req)
        assert res.status_code == 200
        assert len(res.data["issues"]) >= 1

    asyncio.run(_test())


def test_notion_connector():
    async def _test():
        c = NotionConnector()
        req = IntegrationRequest(method="SEARCH_PAGES", params={"query": "Roadmap"})
        res = await c.execute(req)
        assert res.status_code == 200
        assert len(res.data["results"]) >= 1

    asyncio.run(_test())


def test_calendar_connector():
    async def _test():
        c = CalendarConnector()
        req = IntegrationRequest(method="LIST_EVENTS")
        res = await c.execute(req)
        assert res.status_code == 200
        assert len(res.data["items"]) >= 1

    asyncio.run(_test())


def test_database_connector():
    async def _test():
        c = DatabaseServiceConnector(connection_string=":memory:", db_type="sqlite")
        req_schema = IntegrationRequest(method="INSPECT_SCHEMA")
        res_schema = await c.execute(req_schema)
        assert res_schema.status_code == 200
        assert "research_projects" in res_schema.data["tables"]

        req_query = IntegrationRequest(method="QUERY", params={"query": "SELECT * FROM research_projects"})
        res_query = await c.execute(req_query)
        assert res_query.status_code == 200
        assert res_query.data["count"] >= 1

    asyncio.run(_test())


def test_cloud_storage_connector():
    async def _test():
        c = CloudStorageServiceConnector()
        req_list = IntegrationRequest(method="LIST_OBJECTS")
        res_list = await c.execute(req_list)
        assert res_list.status_code == 200
        assert len(res_list.data["objects"]) >= 1

        req_put = IntegrationRequest(method="PUT_OBJECT", params={"key": "test.txt", "content": "Hello Storage"})
        res_put = await c.execute(req_put)
        assert res_put.status_code == 200
        assert res_put.data["status"] == "uploaded"

    asyncio.run(_test())
