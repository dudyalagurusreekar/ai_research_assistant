"""Unit Tests for Unified Storage Package (ArtifactStore and CheckpointStore)."""

import os
import time
import shutil
import unittest
import tempfile
from concurrent.futures import Future

from tools.browser.storage.artifact_store import DiskArtifactStore
from tools.browser.storage.checkpoint_store import DiskCheckpointStore


class TestStorageSystem(unittest.TestCase):
    """Verifies that synchronous and asynchronous operations perform correctly and thread pools write to disk without blockages."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.artifact_store = DiskArtifactStore(artifact_dir=self.temp_dir)
        self.checkpoint_store = DiskCheckpointStore()

    def tearDown(self) -> None:
        self.artifact_store.shutdown()
        self.checkpoint_store.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_artifact_store_sync_write(self):
        """Verify synchronous artifact file creation."""
        data = {"test_key": "test_value"}
        filepath = self.artifact_store.save_artifact_sync("test_artifact", data)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith(".json"))

    def test_artifact_store_async_write(self):
        """Verify asynchronous artifact execution using callbacks."""
        data = {"test_key_async": "value_async"}
        callback_triggered = False
        saved_path = ""

        def callback(path):
            nonlocal callback_triggered, saved_path
            callback_triggered = True
            saved_path = path

        future = self.artifact_store.save_artifact_async("test_async", data, callback=callback)
        self.assertIsInstance(future, Future)
        
        # Wait for async thread worker
        res_path = future.result(timeout=2.0)
        self.assertEqual(res_path, saved_path)
        self.assertTrue(callback_triggered)
        self.assertTrue(os.path.exists(res_path))

    def test_checkpoint_store_sync_save_and_load(self):
        """Verify synchronous checkpoint creation and loader."""
        checkpoint_path = os.path.join(self.temp_dir, "checkpoints", "state.json")
        state_data = {"current_step": 5, "visited": ["http://a.com"]}
        
        self.checkpoint_store.save_checkpoint_sync(state_data, checkpoint_path)
        self.assertTrue(os.path.exists(checkpoint_path))
        
        loaded = self.checkpoint_store.load_checkpoint(checkpoint_path)
        self.assertEqual(loaded, state_data)

    def test_checkpoint_store_async_save(self):
        """Verify asynchronous checkpoint creation."""
        checkpoint_path = os.path.join(self.temp_dir, "checkpoints", "state_async.json")
        state_data = {"current_step": 10, "visited": ["http://b.com"]}
        
        future = self.checkpoint_store.save_checkpoint_async(state_data, checkpoint_path)
        res_path = future.result(timeout=2.0)
        
        self.assertEqual(res_path, checkpoint_path)
        self.assertTrue(os.path.exists(checkpoint_path))
        
        loaded = self.checkpoint_store.load_checkpoint(checkpoint_path)
        self.assertEqual(loaded, state_data)


if __name__ == "__main__":
    unittest.main()
