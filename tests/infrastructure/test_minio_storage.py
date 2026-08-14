import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base
from infrastructure.storage.minio_client import LocalStorageFallback, MinIOClientManager
from infrastructure.storage.storage_manager import ObjectStorageManager


def test_minio_local_fallback(tmp_path):
    storage_fallback = LocalStorageFallback(base_dir=str(tmp_path / ".storage"))
    storage_fallback.make_bucket("ara-uploads")
    assert storage_fallback.bucket_exists("ara-uploads") is True

    import io
    data = b"Hello ARA MinIO Storage"
    storage_fallback.put_object("ara-uploads", "test.txt", io.BytesIO(data), len(data))

    obj = storage_fallback.get_object("ara-uploads", "test.txt")
    assert obj.read() == data


def test_object_storage_manager_store_document(tmp_path):
    # Setup test DB
    db_mgr = DatabaseManager("sqlite:///:memory:")
    db_mgr.create_all_tables(Base)

    # Setup MinIO mock client
    minio_mgr = MinIOClientManager()
    osm = ObjectStorageManager(client_manager=minio_mgr)

    with db_mgr.get_session() as session:
        doc_content = b"PDF Document binary payload content"
        doc = osm.store_document_file(
            workspace_id="ws-test-123",
            title="Quantum Report.pdf",
            content_bytes=doc_content,
            mime_type="application/pdf",
            db_session=session,
        )

        assert doc.id is not None
        assert doc.file_size == len(doc_content)
        assert doc.minio_bucket == "ara-uploads"
        assert doc.sha256_hash == minio_mgr.calculate_sha256(doc_content)

        # Retrieve file bytes back
        bucket, obj_name = doc.storage_path.split("/", 1)
        retrieved_bytes = osm.get_file_content(bucket, obj_name)
        assert retrieved_bytes == doc_content
