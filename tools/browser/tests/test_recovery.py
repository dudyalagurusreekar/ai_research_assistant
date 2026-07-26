"""Unit tests for Browser Recovery Engine."""

import os
import shutil
import unittest
from infrastructure.storage import DiskStorage
from tools.browser.recovery import BrowserRecoveryEngine
from tools.browser.state import BrowserStateModel


class TestBrowserRecovery(unittest.IsolatedAsyncioTestCase):
    """Test checkpoint saving and crash recovery."""

    async def asyncSetUp(self):
        self.test_dir = ".test_browser_recovery_dir"
        storage = DiskStorage(base_dir=self.test_dir)
        self.recovery = BrowserRecoveryEngine(storage=storage)

    async def asyncTearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    async def test_save_and_restore_snapshot(self):
        state = BrowserStateModel(url="https://example.com/dashboard", dom_version_hash="abc12345")
        saved = await self.recovery.save_snapshot("session_test", state)
        self.assertTrue(saved)

        restored = await self.recovery.restore_snapshot("session_test")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.url, "https://example.com/dashboard")


if __name__ == "__main__":
    unittest.main()
