"""PromptManager — manages prompt retrieval, custom template registration, and rendering."""

from typing import Dict, Optional, Any
from core.prompts.templates import PromptTemplate, SystemPromptRegistry
from utils.logger import get_logger

logger = get_logger("PromptManager")


class PromptManager:
    """Production prompt management service."""

    def __init__(self):
        self._registry: Dict[str, PromptTemplate] = {
            "system_researcher": SystemPromptRegistry.SYSTEM_RESEARCHER,
            "system_planner": SystemPromptRegistry.SYSTEM_PLANNER,
            "system_verifier": SystemPromptRegistry.SYSTEM_VERIFIER,
        }

    def register_template(self, template: PromptTemplate) -> None:
        """Register or update a prompt template."""
        self._registry[template.name] = template
        logger.info(f"Registered prompt template: '{template.name}' (v{template.version})")

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Retrieve template by name."""
        return self._registry.get(name)

    def render(self, template_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """Render prompt template by name."""
        tpl = self.get_template(template_name)
        if not tpl:
            logger.warning(f"Prompt template '{template_name}' not found. Falling back to default raw text.")
            return str(variables.get("query", "") if variables else "")
        return tpl.render(variables)


prompt_manager = PromptManager()
