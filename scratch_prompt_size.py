"""Verify the compact prompt and test agent creation."""
from agents.research_agent import create_agent

agent = create_agent()
prompt = agent.system_prompt

print(f"System prompt length: {len(prompt)} chars")
print(f"Estimated tokens: ~{len(prompt) // 4}")
print(f"Word count: {len(prompt.split())}")
print()
print("=== FULL SYSTEM PROMPT ===")
print(prompt)
