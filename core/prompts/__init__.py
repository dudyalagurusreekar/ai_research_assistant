"""Prompt Management Platform for ARA v1.0 — system prompts, templates, and dynamic variable interpolation."""

from core.prompts.manager import PromptManager
from core.prompts.templates import PromptTemplate, SystemPromptRegistry

__all__ = ["PromptManager", "PromptTemplate", "SystemPromptRegistry"]
