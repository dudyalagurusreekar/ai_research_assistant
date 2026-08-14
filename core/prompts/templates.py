"""Prompt Templates and System Prompt Registry for ARA v1.0 AI Engine."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """Structured Prompt Template with metadata, versioning, and variable schema."""

    name: str
    version: str = "1.0.0"
    description: str
    template_text: str
    default_variables: Dict[str, Any] = Field(default_factory=dict)

    def render(self, variables: Optional[Dict[str, Any]] = None) -> str:
        """Render template with supplied variables, falling back to defaults."""
        merged = {**self.default_variables, **(variables or {})}
        rendered = self.template_text
        for key, val in merged.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, str(val))
        return rendered


class SystemPromptRegistry:
    """Central registry of system prompts across research domains."""

    SYSTEM_RESEARCHER = PromptTemplate(
        name="system_researcher",
        version="1.0.0",
        description="Core autonomous researcher system prompt",
        template_text=(
            "You are ARA (AI Research Assistant), an expert autonomous research scientist. "
            "Your objective is: {goal}. "
            "Always maintain rigorous evidence grounding, cite authoritative sources, "
            "and produce clear, objective technical insights."
        ),
        default_variables={"goal": "Conduct rigorous multi-source research"},
    )

    SYSTEM_PLANNER = PromptTemplate(
        name="system_planner",
        version="1.0.0",
        description="Goal decomposition and planning system prompt",
        template_text=(
            "You are the ARA Lead Planning Engine. Deconstruct the research task '{query}' "
            "into a structured execution DAG with minimal step redundancy and optimal parallel waves."
        ),
        default_variables={"query": "Research target domain"},
    )

    SYSTEM_VERIFIER = PromptTemplate(
        name="system_verifier",
        version="1.0.0",
        description="Self-verification and anti-hallucination audit prompt",
        template_text=(
            "Audit the generated response for factual correctness, source alignment, and logical consistency. "
            "Evidence: {evidence}. Output: {output}."
        ),
        default_variables={"evidence": "Retrieved documents", "output": "Generated response"},
    )
