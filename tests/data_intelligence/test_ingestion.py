"""Unit tests for DataIngestionModule."""

import os
import json
import tempfile
import sqlite3
import pytest
from core.data_intelligence.components.ingestion import DataIngestionModule


@pytest.fixture
def temp_files():
    tmp_dir = tempfile.mkdtemp()
    
    # CSV file
    csv_path = os.path.join(tmp_dir, "sample.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("name,age,salary\nAlice,30,75000\nBob,25,50000\nCharlie,35,90000\n")

    # JSON file
    json_path = os.path.join(tmp_dir, "sample.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([{"product": "Laptop", "price": 1200}, {"product": "Phone", "price": 800}], f)

    # SQLite file
    db_path = os.path.join(tmp_dir, "sample.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE sales (region TEXT, revenue REAL)")
    cursor.execute("INSERT INTO sales VALUES ('North', 1000.0), ('South', 1500.0)")
    conn.commit()
    conn.close()

    yield csv_path, json_path, db_path
    import shutil
    shutil.rmtree(tmp_dir)


def test_ingestion_csv(temp_files):
    csv_path, _, _ = temp_files
    ingestion = DataIngestionModule()
    records = ingestion.load_csv(csv_path)
    assert len(records) == 3
    assert records[0]["name"] == "Alice"
    assert records[0]["age"] == 30


def test_ingestion_json(temp_files):
    _, json_path, _ = temp_files
    ingestion = DataIngestionModule()
    records = ingestion.load_json(json_path)
    assert len(records) == 2
    assert records[0]["product"] == "Laptop"


def test_ingestion_sqlite(temp_files):
    _, _, db_path = temp_files
    ingestion = DataIngestionModule()
    records = ingestion.load_sqlite(db_path, "sales")
    assert len(records) == 2
    assert records[0]["region"] == "North"
