"""Episodic Memory Engine — Records and recalls execution episodes for learning from past workflows."""

from __future__ import annotations

import re
import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger("EpisodicMemoryEngine")


@dataclass
class Episode:
    """A single execution episode recording a complete research workflow."""

    episode_id: str = field(default_factory=lambda: f"ep_{uuid.uuid4().hex[:10]}")
    user_id: str = ""
    project_id: str = ""
    query: str = ""
    plan_steps: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    sources_consulted: List[str] = field(default_factory=list)
    outcome: str = ""
    success: bool = True
    confidence_score: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "query": self.query,
            "plan_steps": self.plan_steps,
            "tools_used": self.tools_used,
            "sources_consulted": self.sources_consulted,
            "outcome": self.outcome,
            "success": self.success,
            "confidence_score": self.confidence_score,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class EpisodicMemoryEngine:
    """Records execution episodes and recalls similar past workflows for learning."""

    def __init__(self) -> None:
        self._episodes: Dict[str, Episode] = {}

    def record_episode(
        self,
        query: str,
        plan_steps: Optional[List[str]] = None,
        tools_used: Optional[List[str]] = None,
        sources_consulted: Optional[List[str]] = None,
        outcome: str = "",
        success: bool = True,
        confidence_score: float = 1.0,
        user_id: str = "",
        project_id: str = "",
        duration_ms: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> Episode:
        """Record a completed execution episode."""
        episode = Episode(
            user_id=user_id,
            project_id=project_id,
            query=query,
            plan_steps=plan_steps or [],
            tools_used=tools_used or [],
            sources_consulted=sources_consulted or [],
            outcome=outcome,
            success=success,
            confidence_score=confidence_score,
            duration_ms=duration_ms,
            tags=tags or [],
        )
        self._episodes[episode.episode_id] = episode
        logger.info(f"Recorded episode '{episode.episode_id}': query='{query[:50]}', success={success}")
        return episode

    def recall_similar_episodes(self, query: str, limit: int = 5) -> List[Episode]:
        """Recall past episodes similar to the given query using keyword overlap."""
        query_words = set(re.findall(r"\w+", query.lower()))
        scored: List[tuple] = []

        for episode in self._episodes.values():
            ep_words = set(re.findall(r"\w+", episode.query.lower()))
            overlap = len(query_words.intersection(ep_words))
            if overlap > 0:
                score = overlap / max(len(query_words.union(ep_words)), 1)
                scored.append((episode, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        results = [ep for ep, _ in scored[:limit]]
        logger.debug(f"Recalled {len(results)} similar episodes for query '{query[:40]}'")
        return results

    def get_episode(self, episode_id: str) -> Optional[Episode]:
        """Retrieve a specific episode by ID."""
        return self._episodes.get(episode_id)

    def list_episodes(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        success_only: bool = False,
        limit: int = 50,
    ) -> List[Episode]:
        """List episodes filtered by user, project, or success status."""
        results = list(self._episodes.values())

        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if project_id:
            results = [e for e in results if e.project_id == project_id]
        if success_only:
            results = [e for e in results if e.success]

        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]

    def delete_episode(self, episode_id: str) -> bool:
        """Delete a specific episode."""
        if episode_id in self._episodes:
            del self._episodes[episode_id]
            return True
        return False

    def purge_user_episodes(self, user_id: str) -> int:
        """Purge all episodic execution records for a user ID."""
        to_del = [ep_id for ep_id, ep in self._episodes.items() if ep.user_id == user_id]
        for ep_id in to_del:
            del self._episodes[ep_id]
        logger.info(f"Purged {len(to_del)} user episodes for user '{user_id}'")
        return len(to_del)

    def purge_project_episodes(self, project_id: str) -> int:
        """Purge all episodic execution records for a project ID."""
        to_del = [ep_id for ep_id, ep in self._episodes.items() if ep.project_id == project_id]
        for ep_id in to_del:
            del self._episodes[ep_id]
        logger.info(f"Purged {len(to_del)} project episodes for project '{project_id}'")
        return len(to_del)

    @property
    def episode_count(self) -> int:
        return len(self._episodes)

