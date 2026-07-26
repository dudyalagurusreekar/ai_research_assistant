"""Unit tests for Context Builder."""

import unittest
from infrastructure.context import ContextBuilder
from core.models import Artifact


class TestContextBuilder(unittest.TestCase):
    """Test context construction, history compression, and artifact injection."""

    def test_build_context(self):
        cb = ContextBuilder(max_token_budget=1000)
        cb.set_system_prompt("System instruction")
        cb.add_history("user", "Hello")
        cb.add_history("assistant", "Hi there")

        art = Artifact(name="summary.pdf", artifact_type="pdf")
        cb.inject_artifact(art)

        ctx = cb.build_context("How are you?")
        self.assertEqual(ctx[0]["role"], "system")
        self.assertEqual(ctx[-1]["role"], "user")
        self.assertEqual(ctx[-1]["content"], "How are you?")


if __name__ == "__main__":
    unittest.main()
