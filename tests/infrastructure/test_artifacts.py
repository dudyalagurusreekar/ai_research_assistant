"""Unit tests for Artifact Store."""

import os
import shutil
import unittest
from infrastructure.artifacts import ArtifactStore
from infrastructure.storage import DiskStorage


class TestArtifactStore(unittest.IsolatedAsyncioTestCase):
    """Test artifact saving, retrieval, and filtering."""

    async def asyncSetUp(self):
        self.test_dir = ".test_artifact_store_dir"
        storage = DiskStorage(base_dir=self.test_dir)
        self.store = ArtifactStore(storage=storage)

    async def asyncTearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    async def test_save_and_get_artifact(self):
        art = await self.store.save_artifact("page.html", "html", "<html></html>", mime_type="text/html")
        self.assertTrue(art.artifact_id.startswith("art_"))

        retrieved = await self.store.get_artifact(art.artifact_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "page.html")

        all_html = await self.store.list_artifacts(artifact_type="html")
        self.assertEqual(len(all_html), 1)


if __name__ == "__main__":
    unittest.main()
