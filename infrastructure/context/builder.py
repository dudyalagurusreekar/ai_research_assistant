"""Context Builder for managing prompt construction, token budgeting, compression, and artifact injection."""

from typing import Any, Dict, List, Optional
from core.models.artifact import Artifact


class ContextBuilder:
    """Constructs minimal, token-budgeted prompt contexts enriched with system instructions and artifacts."""

    def __init__(self, max_token_budget: int = 4000) -> None:
        self.max_token_budget = max_token_budget
        self._system_prompt: str = "You are a helpful AI research assistant."
        self._history: List[Dict[str, str]] = []
        self._artifacts: List[Artifact] = []

    def set_system_prompt(self, prompt: str) -> None:
        """Define system prompt instruction."""
        self._system_prompt = prompt

    def add_history(self, role: str, content: str) -> None:
        """Append message to turn history."""
        self._history.append({"role": role, "content": content})

    def inject_artifact(self, artifact: Artifact) -> None:
        """Inject an artifact descriptor into prompt context."""
        self._artifacts.append(artifact)

    def estimate_tokens(self, text: str) -> int:
        """Heuristically estimate token count (approx. 4 chars per token)."""
        return max(1, len(text) // 4)

    def compress_history(self, max_turns: int = 5) -> List[Dict[str, str]]:
        """Select and compress history turns to fit within recent window."""
        if len(self._history) <= max_turns:
            return self._history
        # Retain first system instruction if any and most recent max_turns
        return self._history[-max_turns:]

    def build_context(self, user_query: str) -> List[Dict[str, str]]:
        """Assemble full messages context within token budget constraints."""
        messages: List[Dict[str, str]] = [{"role": "system", "content": self._system_prompt}]

        # Inject artifact summaries
        if self._artifacts:
            art_text = "Injected Artifacts:\n" + "\n".join(
                [f"- [{a.artifact_type}] {a.name} (ID: {a.artifact_id})" for a in self._artifacts]
            )
            messages.append({"role": "system", "content": art_text})

        # Add compressed history
        compressed = self.compress_history()
        messages.extend(compressed)

        # Add user query
        messages.append({"role": "user", "content": user_query})

        # Enforce total token budget truncation if needed
        total_tokens = sum(self.estimate_tokens(m["content"]) for m in messages)
        if total_tokens > self.max_token_budget:
            # Simple truncation of user query or oldest non-system history
            user_msg = messages.pop()
            budget_for_user = max(100, self.max_token_budget - sum(self.estimate_tokens(m["content"]) for m in messages))
            truncated_content = user_msg["content"][: budget_for_user * 4]
            messages.append({"role": "user", "content": truncated_content})

        return messages
