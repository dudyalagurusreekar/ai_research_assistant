"""ExperienceStore for persistent storage, indexing, and querying of execution records."""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from core.learning.models.context import ExperienceRecord, ExperienceOutcome

logger = get_logger("ExperienceStore")


class ExperienceStore:
    """JSON file-backed persistent store for historical execution records."""

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), ".storage", "experience")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.storage_dir / "experience_records.json"
        self._records: Dict[str, ExperienceRecord] = {}
        self.load()

    def load(self) -> None:
        """Loads records from the JSON store file."""
        if not self.store_file.exists():
            self._records = {}
            return

        try:
            with open(self.store_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._records = {
                    rec_id: ExperienceRecord.from_dict(rec_data)
                    for rec_id, rec_data in data.items()
                }
            logger.info(f"Loaded {len(self._records)} experience records from {self.store_file}")
        except Exception as e:
            logger.error(f"Failed to load experience records from {self.store_file}: {e}")
            self._records = {}

    def save(self) -> None:
        """Saves current records to the JSON store file."""
        try:
            data = {rec_id: rec.to_dict() for rec_id, rec in self._records.items()}
            with open(self.store_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._records)} experience records to {self.store_file}")
        except Exception as e:
            logger.error(f"Failed to save experience records to {self.store_file}: {e}")

    def add_record(self, record: ExperienceRecord) -> None:
        """Adds a new experience record and persists to disk."""
        self._records[record.record_id] = record
        self.save()

    def get_record(self, record_id: str) -> Optional[ExperienceRecord]:
        """Retrieves a record by ID."""
        return self._records.get(record_id)

    def list_records(self) -> List[ExperienceRecord]:
        """Returns all records sorted by timestamp descending."""
        records = list(self._records.values())
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records

    def find_similar_records(
        self, query: str, intent: Optional[str] = None, limit: int = 5
    ) -> List[ExperienceRecord]:
        """Finds historical records matching query keywords and/or intent."""
        records = self.list_records()
        query_words = set(query.lower().split())

        scored_records = []
        for r in records:
            score = 0.0
            if intent and r.intent and intent.lower() == r.intent.lower():
                score += 3.0

            r_words = set(r.query.lower().split())
            common = query_words.intersection(r_words)
            if query_words:
                overlap = len(common) / len(query_words)
                score += overlap * 2.0

            if r.outcome == ExperienceOutcome.SUCCESS:
                score += 1.0

            scored_records.append((score, r))

        scored_records.sort(key=lambda x: x[0], reverse=True)
        return [r for score, r in scored_records if score > 0.5][:limit]

    def get_records_by_intent(self, intent: str) -> List[ExperienceRecord]:
        """Returns records matching a specific intent."""
        return [
            r for r in self._records.values()
            if r.intent and r.intent.lower() == intent.lower()
        ]

    def clear(self) -> None:
        """Clears all stored records (reversibility guarantee)."""
        self._records.clear()
        if self.store_file.exists():
            try:
                os.remove(self.store_file)
            except Exception as e:
                logger.error(f"Failed to remove experience file: {e}")
        logger.info("ExperienceStore cleared.")

    def export_data(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._records.values()]

    def count(self) -> int:
        return len(self._records)
