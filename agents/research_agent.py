from smolagents import CodeAgent

from config.model import get_model
from tools import registry


def create_agent():
    return CodeAgent(
        model=get_model(),
        tools=registry.get_tools(),
        max_steps=3,
        additional_authorized_imports=[],
    )