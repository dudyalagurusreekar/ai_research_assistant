"""Unit tests for Storage Layer."""

import os
import shutil
import unittest
from infrastructure.storage import DiskStorage


class TestDiskStorage(unittest.IsolatedAsyncioTestCase):
    """Test async storage read/write and checkpointing."""

    async def asyncSetUp(self):
        self.test_dir = ".test_storage_dir"
        self.storage = DiskStorage(base_dir=self.test_dir)

    async def asyncTearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    async def test_read_write_delete(self):
        success = await self.storage.write("session_data", {"foo": "bar"})
        self.assertTrue(success)

        data = await self.storage.read("session_data")
        self.assertEqual(data, {"foo": "bar"})

        del_success = await self.storage.delete("session_data")
        self.assertTrue(del_success)
        self.assertIsNone(await self.storage.read("session_data"))

    async def test_checkpoints(self):
        await self.storage.save_checkpoint("chk_1", {"step": 5})
        chk = await self.storage.load_checkpoint("chk_1")
        self.assertEqual(chk, {"step": 5})


if __name__ == "__main__":
    unittest.main()
