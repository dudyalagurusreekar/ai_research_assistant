"""Unit tests for Shared Models."""

import unittest
from core.models import (
    ToolMetadata,
    Artifact,
    ToolResult,
    Request,
    Response,
    ResponseStatus,
    Session,
    SessionState,
    Event,
)


class TestModels(unittest.TestCase):
    """Test data model initialization and serialization."""

    def test_tool_metadata(self):
        meta = ToolMetadata(
            name="test_tool",
            version="1.0.0",
            description="Test Tool Description",
            capabilities=["test", "demo"],
        )
        self.assertEqual(meta.name, "test_tool")
        d = meta.to_dict()
        self.assertEqual(d["name"], "test_tool")
        self.assertEqual(d["capabilities"], ["test", "demo"])

    def test_artifact_model(self):
        art = Artifact(name="report.pdf", artifact_type="pdf", content=b"PDFDATA")
        self.assertTrue(art.artifact_id.startswith("art_"))
        d = art.to_dict()
        self.assertEqual(d["name"], "report.pdf")

    def test_tool_result_model(self):
        art = Artifact(name="out.txt", artifact_type="text")
        res = ToolResult(tool_name="test_tool", success=True, data={"res": 42}, artifacts=[art])
        self.assertTrue(res.success)
        d = res.to_dict()
        self.assertEqual(len(d["artifacts"]), 1)

    def test_request_response_model(self):
        req = Request(intent="search_data", session_id="sess_123")
        self.assertTrue(req.request_id.startswith("req_"))

        resp = Response(
            request_id=req.request_id,
            session_id=req.session_id,
            status=ResponseStatus.SUCCESS,
            data={"result": "found"},
        )
        self.assertEqual(resp.status, ResponseStatus.SUCCESS)
        d = resp.to_dict()
        self.assertEqual(d["status"], "success")

    def test_session_model(self):
        sess = Session(user_id="user_42")
        self.assertTrue(sess.session_id.startswith("sess_"))
        self.assertEqual(sess.state, SessionState.CREATED)

        sess.update_state(SessionState.RUNNING)
        self.assertEqual(sess.state, SessionState.RUNNING)
        d = sess.to_dict()
        self.assertEqual(d["state"], "running")

    def test_event_model(self):
        evt = Event(event_type="test.event", source="unit_test", payload={"foo": "bar"})
        self.assertTrue(evt.event_id.startswith("evt_"))
        d = evt.to_dict()
        self.assertEqual(d["event_type"], "test.event")


if __name__ == "__main__":
    unittest.main()
