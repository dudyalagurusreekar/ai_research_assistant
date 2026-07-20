from smolagents import CodeAgent
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.model import get_model
from tools.registry import registry


agent = CodeAgent(
    tools=registry.get_tools(),
    model=get_model(),
    max_steps=1,
)

print("Agent created successfully.")

result = agent.run("What is 2 + 2?")

print(result)