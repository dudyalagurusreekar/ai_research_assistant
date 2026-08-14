"""Unit tests for ExperienceStore."""

import os
import shutil
import tempfile
import pytest
from core.learning.components.experience_store import ExperienceStore
from core.learning.models.context import ExperienceRecord, ExperienceOutcome


@pytest.fixture
def temp_store():
    tmp_dir = tempfile.mkdtemp()
    store = ExperienceStore(storage_dir=tmp_dir)
    yield store
    shutil.rmtree(tmp_dir)


def test_experience_store_add_get_list(temp_store):
    rec = ExperienceRecord(
        query="Research quantum computing",
        intent="multi_step_research",
        selected_tools=["search_tool", "document_tool"],
        outcome=ExperienceOutcome.SUCCESS,
    )
    temp_store.add_record(rec)

    assert temp_store.count() == 1
    fetched = temp_store.get_record(rec.record_id)
    assert fetched is not None
    assert fetched.query == "Research quantum computing"
    assert fetched.intent == "multi_step_research"
    assert len(fetched.selected_tools) == 2


def test_experience_store_similarity_search(temp_store):
    rec1 = ExperienceRecord(
        query="Solid state battery research 2024",
        intent="multi_step_research",
        selected_tools=["search_tool"],
        outcome=ExperienceOutcome.SUCCESS,
    )
    rec2 = ExperienceRecord(
        query="Quantum computing papers comparison",
        intent="comparison",
        selected_tools=["search_tool", "report_tool"],
        outcome=ExperienceOutcome.SUCCESS,
    )
    temp_store.add_record(rec1)
    temp_store.add_record(rec2)

    matches = temp_store.find_similar_records("quantum computing", intent="comparison")
    assert len(matches) >= 1
    assert matches[0].record_id == rec2.record_id


def test_experience_store_clear(temp_store):
    rec = ExperienceRecord(query="Test query", intent="general_qa")
    temp_store.add_record(rec)
    assert temp_store.count() == 1

    temp_store.clear()
    assert temp_store.count() == 0
