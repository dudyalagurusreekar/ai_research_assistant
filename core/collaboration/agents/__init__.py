"""Agents package for multi-agent collaboration framework."""

from core.collaboration.agents.base import BaseSpecializedAgent
from core.collaboration.agents.code_agent import SpecializedCodeAgent
from core.collaboration.agents.data_agent import SpecializedDataAgent
from core.collaboration.agents.research_agent import SpecializedResearchAgent
from core.collaboration.agents.reviewer_agent import SpecializedReviewerAgent
from core.collaboration.agents.writer_agent import SpecializedWriterAgent

__all__ = [
    "BaseSpecializedAgent",
    "SpecializedResearchAgent",
    "SpecializedDataAgent",
    "SpecializedCodeAgent",
    "SpecializedWriterAgent",
    "SpecializedReviewerAgent",
]
