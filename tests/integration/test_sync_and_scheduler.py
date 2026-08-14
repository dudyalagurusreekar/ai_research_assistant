"""Unit tests for SyncEngine, Watermarks, Change Detection, Scheduler, and Cache Layer."""

import pytest
import asyncio
import os

from tools.integration.sync.sync_engine import SynchronizationEngine, WatermarkTracker, SyncMode
from tools.integration.change_detection.change_detector import ChangeDetectionEngine, EntityDiffer
from tools.integration.scheduler.scheduler import IntegrationScheduler
from tools.integration.cache.cache_layer import IntegrationCache


def test_watermark_tracker_and_sync_engine():
    wm_path = ".storage/test_wm.json"
    tracker = WatermarkTracker(store_path=wm_path)
    engine = SynchronizationEngine(tracker=tracker)

    chk = engine.start_sync(service_name="gmail", entity_type="messages", mode=SyncMode.INCREMENTAL)
    assert chk.status == "in_progress"

    engine.record_sync_progress(chk.checkpoint_id, records_fetched=10, next_sync_token="token_v2")
    comp = engine.complete_sync(chk.checkpoint_id)
    assert comp.status == "completed"

    wm = tracker.get_watermark("gmail", "messages")
    assert wm.records_synced == 10
    assert wm.sync_token == "token_v2"

    if os.path.exists(wm_path):
        os.remove(wm_path)


def test_entity_differ():
    old_e = {"id": "1", "title": "Old Title", "status": "open"}
    new_e = {"id": "1", "title": "New Title", "status": "open"}

    diff = EntityDiffer.compute_diff(old_e, new_e)
    assert "title" in diff
    assert diff["title"]["old"] == "Old Title"
    assert diff["title"]["new"] == "New Title"
    assert "status" not in diff


def test_scheduler_execution():
    async def _test():
        sched = IntegrationScheduler()
        executed_jobs = []

        def _dummy_job(job):
            executed_jobs.append(job.job_id)

        sched.add_job("job_01", service_name="gmail", action="sync", interval_seconds=0.01)
        await asyncio.sleep(0.02)

        records = await sched.run_pending_jobs(_dummy_job)
        assert len(records) >= 1
        assert "job_01" in executed_jobs

    asyncio.run(_test())


def test_cache_layer():
    cache_dir = ".storage/test_cache_dir"
    cache = IntegrationCache(cache_dir=cache_dir, default_ttl_seconds=60)

    cache.set(service="github", endpoint="/user", data={"name": "ara_bot"}, params={"id": 1})
    val = cache.get(service="github", endpoint="/user", params={"id": 1})
    assert val["name"] == "ara_bot"

    inv_count = cache.invalidate_service("github")
    assert inv_count >= 1
    assert cache.get(service="github", endpoint="/user", params={"id": 1}) is None
