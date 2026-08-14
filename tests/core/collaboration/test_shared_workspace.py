"""Unit tests for SharedWorkspace state management and artifact store."""

import pytest

from core.collaboration.components.workspace import SharedWorkspace


def test_workspace_set_get_and_has():
    workspace = SharedWorkspace(workspace_id="test_ws")

    workspace.set("metric_score", 0.95, agent_id="data_agent", artifact_type="data", tags=["perf"])
    assert workspace.has("metric_score") is True
    assert workspace.get("metric_score") == 0.95

    art = workspace.get_artifact("metric_score")
    assert art.created_by_agent == "data_agent"
    assert art.version == 1
    assert "perf" in art.tags


def test_workspace_versioning_and_overwrite():
    workspace = SharedWorkspace(workspace_id="test_ws")

    workspace.set("summary", "Initial draft", agent_id="agent_1")
    art1 = workspace.get_artifact("summary")
    assert art1.version == 1
    assert art1.value == "Initial draft"

    workspace.set("summary", "Updated draft", agent_id="agent_2")
    art2 = workspace.get_artifact("summary")
    assert art2.version == 2
    assert art2.value == "Updated draft"
    assert art2.created_by_agent == "agent_2"


def test_workspace_list_keys_and_delete():
    workspace = SharedWorkspace(workspace_id="test_ws")

    workspace.set("key_1", "val1", artifact_type="text")
    workspace.set("key_2", "val2", artifact_type="data")
    workspace.set("key_3", "val3", artifact_type="text")

    text_keys = workspace.list_keys(artifact_type="text")
    assert len(text_keys) == 2
    assert "key_1" in text_keys and "key_3" in text_keys

    workspace.delete("key_1")
    assert workspace.has("key_1") is False
    assert len(workspace.list_keys(artifact_type="text")) == 1
