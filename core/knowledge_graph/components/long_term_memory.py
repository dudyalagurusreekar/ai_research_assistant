"""Long-Term Memory Store — Persistent user and project scoped memory with importance scoring."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger("LongTermMemoryStore")


class MemoryScope(Enum):
    """Scope of a memory entry."""
    USER = "user"
    PROJECT = "project"
    SYSTEM = "system"


class DataSensitivity(Enum):
    """Privacy sensitivity level of stored memory."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class MemoryEntry:
    """A single persistent memory entry."""

    memory_id: str = field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:10]}")
    scope: MemoryScope = MemoryScope.USER
    owner_id: str = ""
    key: str = ""
    value: str = ""
    importance_score: float = 0.5
    access_count: int = 0
    sensitivity: DataSensitivity = DataSensitivity.PUBLIC
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "scope": self.scope.value,
            "owner_id": self.owner_id,
            "key": self.key,
            "value": self.value,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "sensitivity": self.sensitivity.value if hasattr(self.sensitivity, "value") else str(self.sensitivity),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "tags": self.tags,
            "metadata": self.metadata,
        }


    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            exp_dt = datetime.fromisoformat(self.expires_at)
            return datetime.now(timezone.utc) > exp_dt
        except Exception:
            return False


class LongTermMemoryStore:
    """Manages persistent user and project scoped memories with importance scoring and expiration."""

    def __init__(self) -> None:
        self._memories: Dict[str, MemoryEntry] = {}

    def store_user_memory(
        self, user_id: str, key: str, value: str,
        importance: float = 0.5, tags: Optional[List[str]] = None,
        ttl_days: Optional[int] = None,
    ) -> MemoryEntry:
        """Store a user-scoped memory entry."""
        expires_at = None
        if ttl_days:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=ttl_days)).isoformat()

        # Check for existing key update
        for mem in self._memories.values():
            if mem.scope == MemoryScope.USER and mem.owner_id == user_id and mem.key == key:
                mem.value = value
                mem.importance_score = max(mem.importance_score, importance)
                mem.access_count += 1
                mem.updated_at = datetime.now(timezone.utc).isoformat()
                if ttl_days:
                    mem.expires_at = expires_at
                logger.info(f"Updated user memory '{key}' for user '{user_id}'")
                return mem

        entry = MemoryEntry(
            scope=MemoryScope.USER,
            owner_id=user_id,
            key=key,
            value=value,
            importance_score=importance,
            tags=tags or [],
            expires_at=expires_at,
        )
        self._memories[entry.memory_id] = entry
        logger.info(f"Stored user memory '{key}' for user '{user_id}'")
        return entry

    def store_project_memory(
        self, project_id: str, key: str, value: str,
        importance: float = 0.5, tags: Optional[List[str]] = None,
        ttl_days: Optional[int] = None,
    ) -> MemoryEntry:
        """Store a project-scoped memory entry."""
        expires_at = None
        if ttl_days:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=ttl_days)).isoformat()

        for mem in self._memories.values():
            if mem.scope == MemoryScope.PROJECT and mem.owner_id == project_id and mem.key == key:
                mem.value = value
                mem.importance_score = max(mem.importance_score, importance)
                mem.access_count += 1
                mem.updated_at = datetime.now(timezone.utc).isoformat()
                if ttl_days:
                    mem.expires_at = expires_at
                logger.info(f"Updated project memory '{key}' for project '{project_id}'")
                return mem

        entry = MemoryEntry(
            scope=MemoryScope.PROJECT,
            owner_id=project_id,
            key=key,
            value=value,
            importance_score=importance,
            tags=tags or [],
            expires_at=expires_at,
        )
        self._memories[entry.memory_id] = entry
        logger.info(f"Stored project memory '{key}' for project '{project_id}'")
        return entry

    def recall_user_memory(self, user_id: str, key_or_query: Optional[str] = None) -> List[MemoryEntry]:
        """Recall user-scoped memories, optionally filtered by key or keyword search."""
        results = [m for m in self._memories.values()
                   if m.scope == MemoryScope.USER and m.owner_id == user_id and not m.is_expired]
        if key_or_query:
            exact = [m for m in results if m.key == key_or_query]
            if exact:
                for m in exact:
                    m.access_count += 1
                return exact
            # Keyword search
            q_words = set(re.findall(r"\w+", key_or_query.lower()))
            results = [m for m in results if q_words.intersection(set(re.findall(r"\w+", (m.key + " " + m.value).lower())))]

        for m in results:
            m.access_count += 1
        return sorted(results, key=lambda m: m.importance_score, reverse=True)

    def recall_project_memory(self, project_id: str, key_or_query: Optional[str] = None) -> List[MemoryEntry]:
        """Recall project-scoped memories, optionally filtered by key or keyword search."""
        results = [m for m in self._memories.values()
                   if m.scope == MemoryScope.PROJECT and m.owner_id == project_id and not m.is_expired]
        if key_or_query:
            exact = [m for m in results if m.key == key_or_query]
            if exact:
                for m in exact:
                    m.access_count += 1
                return exact
            q_words = set(re.findall(r"\w+", key_or_query.lower()))
            results = [m for m in results if q_words.intersection(set(re.findall(r"\w+", (m.key + " " + m.value).lower())))]

        for m in results:
            m.access_count += 1
        return sorted(results, key=lambda m: m.importance_score, reverse=True)

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory entry by ID."""
        if memory_id in self._memories:
            del self._memories[memory_id]
            logger.info(f"Deleted memory '{memory_id}'")
            return True
        return False

    def list_memories(
        self, scope: Optional[MemoryScope] = None,
        owner_id: Optional[str] = None, limit: int = 50,
    ) -> List[MemoryEntry]:
        """List memory entries with optional scope/owner filtering."""
        results = list(self._memories.values())
        if scope:
            results = [m for m in results if m.scope == scope]
        if owner_id:
            results = [m for m in results if m.owner_id == owner_id]
        results = [m for m in results if not m.is_expired]
        results.sort(key=lambda m: m.importance_score, reverse=True)
        return results[:limit]

    @property
    def total_count(self) -> int:
        return len(self._memories)

    def user_memory_count(self, user_id: Optional[str] = None) -> int:
        mems = [m for m in self._memories.values() if m.scope == MemoryScope.USER]
        if user_id:
            mems = [m for m in mems if m.owner_id == user_id]
        return len(mems)

    def project_memory_count(self, project_id: Optional[str] = None) -> int:
        mems = [m for m in self._memories.values() if m.scope == MemoryScope.PROJECT]
        if project_id:
            mems = [m for m in mems if m.owner_id == project_id]
        return len(mems)

    @staticmethod
    def redact_pii(text: str) -> str:
        """Redact common PII patterns (email, phone, SSN, API keys) from text."""
        # Email address
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]", text)
        # Phone number (US format)
        text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]", text)
        # API Keys (e.g. sk-..., bearer tokens)
        text = re.sub(r"\b(sk-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9._\-]{20,})\b", "[REDACTED_KEY]", text)
        return text

    def purge_user_data(self, user_id: str) -> int:
        """Hard purge all memory records belonging to a user ID."""
        to_delete = [
            m_id for m_id, m in self._memories.items()
            if m.scope == MemoryScope.USER and m.owner_id == user_id
        ]
        for m_id in to_delete:
            del self._memories[m_id]
        logger.info(f"Purged {len(to_delete)} user memory records for user '{user_id}'")
        return len(to_delete)

    def purge_project_data(self, project_id: str) -> int:
        """Hard purge all memory records belonging to a project ID."""
        to_delete = [
            m_id for m_id, m in self._memories.items()
            if m.scope == MemoryScope.PROJECT and m.owner_id == project_id
        ]
        for m_id in to_delete:
            del self._memories[m_id]
        logger.info(f"Purged {len(to_delete)} project memory records for project '{project_id}'")
        return len(to_delete)

    def redact_memory(self, memory_id: str) -> bool:
        """Redact PII from a stored memory entry's value."""
        if memory_id in self._memories:
            mem = self._memories[memory_id]
            mem.value = self.redact_pii(mem.value)
            mem.updated_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Redacted PII in memory record '{memory_id}'")
            return True
        return False

