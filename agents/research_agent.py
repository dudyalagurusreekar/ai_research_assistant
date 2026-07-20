from pathlib import Path

import yaml
from smolagents import CodeAgent

from config import get_model, get_research_agent_config
from tools import registry

# Path to the compact prompt template (80% smaller than the smolagents default)
_COMPACT_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "compact_code_agent.yaml"


def _load_compact_prompts() -> dict:
    """Load the compact prompt templates from YAML."""
    return yaml.safe_load(_COMPACT_PROMPT_PATH.read_text(encoding="utf-8"))


class ResearchAgent:
    """
    Builds and manages the Research CodeAgent.
    """

    def __init__(self):
        self.config = get_research_agent_config()
        self.model = get_model()
        self.tools = registry.get_tools()

    def build(self) -> CodeAgent:
        return CodeAgent(
            model=self.model,
            tools=self.tools,
            prompt_templates=_load_compact_prompts(),
            max_steps=self.config.max_steps,
            planning_interval=self.config.planning_interval,
            additional_authorized_imports=self.config.authorized_imports,
            stream_outputs=self.config.stream_outputs,
            use_structured_outputs_internally=self.config.use_structured_outputs_internally,
            max_print_outputs_length=self.config.max_print_outputs_length,
        )


def create_agent() -> CodeAgent:
    """
    Backward-compatible factory.
    """
    return ResearchAgent().build()