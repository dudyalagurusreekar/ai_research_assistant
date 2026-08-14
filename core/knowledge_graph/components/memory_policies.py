"""Memory Policy Engine — Expiration enforcement, importance scoring, privacy controls."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger("MemoryPolicyEngine")


class MemoryPolicyEngine:
    """Enforces memory lifecycle policies: expiration, importance scoring, user-controlled deletion, and privacy."""

    def __init__(
        self,
        default_ttl_days: int = 90,
        min_importance_threshold: float = 0.1,
    ) -> None:
        self.default_ttl_days = default_ttl_days
        self.min_importance_threshold = min_importance_threshold

    def enforce_expiration(self, memory_store: Any) -> int:
        """Remove expired memories from the memory store."""
        if not hasattr(memory_store, '_memories'):
            return 0

        expired_ids = []
        for mem_id, mem in memory_store._memories.items():
            if hasattr(mem, 'is_expired') and mem.is_expired:
                expired_ids.append(mem_id)

        for mem_id in expired_ids:
            memory_store.delete_memory(mem_id)

        if expired_ids:
            logger.info(f"MemoryPolicyEngine expired {len(expired_ids)} memory entries")
        return len(expired_ids)

    def compute_importance_scores(self, memory_store: Any) -> int:
        """Recalculate importance scores based on access frequency and recency."""
        if not hasattr(memory_store, '_memories'):
            return 0

        updated = 0
        now = datetime.now(timezone.utc)

        for mem in memory_store._memories.values():
            access_boost = min(0.3, mem.access_count * 0.05)

            # Recency factor: more recent = higher score
            try:
                created = datetime.fromisoformat(mem.created_at)
                age_days = max(1, (now - created).days)
                recency_factor = min(1.0, 30.0 / age_days)
            except Exception:
                recency_factor = 0.5

            new_importance = min(1.0, (mem.importance_score * 0.6) + (access_boost * 0.2) + (recency_factor * 0.2))
            mem.importance_score = round(new_importance, 4)
            updated += 1

        logger.debug(f"MemoryPolicyEngine recalculated importance for {updated} memories")
        return updated

    def apply_privacy_controls(self, memory_store: Any, user_id: str, deletion_scope: str = "all") -> int:
        """GDPR-style right-to-forget: delete all memories belonging to a user."""
        if not hasattr(memory_store, '_memories'):
            return 0

        to_delete = []
        for mem_id, mem in memory_store._memories.items():
            if mem.owner_id == user_id:
                if deletion_scope == "all" or mem.scope.value == deletion_scope:
                    to_delete.append(mem_id)

        for mem_id in to_delete:
            memory_store.delete_memory(mem_id)

        logger.info(f"MemoryPolicyEngine privacy deletion: removed {len(to_delete)} memories for user '{user_id}'")
        return len(to_delete)

    def prune_low_importance(self, memory_store: Any) -> int:
        """Remove memories below the minimum importance threshold."""
        if not hasattr(memory_store, '_memories'):
            return 0

        to_prune = [
            mem_id for mem_id, mem in memory_store._memories.items()
            if mem.importance_score < self.min_importance_threshold
        ]

        for mem_id in to_prune:
            memory_store.delete_memory(mem_id)

        if to_prune:
            logger.info(f"MemoryPolicyEngine pruned {len(to_prune)} low-importance memories (threshold={self.min_importance_threshold})")
        return len(to_prune)

    def get_policy_summary(self) -> Dict[str, Any]:
        """Return current policy configuration."""
        return {
            "default_ttl_days": self.default_ttl_days,
            "min_importance_threshold": self.min_importance_threshold,
            "policies": [
                "expiration_enforcement",
                "importance_scoring",
                "privacy_controls",
                "low_importance_pruning",
            ],
        }
