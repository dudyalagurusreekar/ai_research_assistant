import unittest
from unittest.mock import MagicMock, patch
from smolagents.local_python_executor import CodeOutput
from smolagents.models import get_clean_message_list
from agents.runtime.agent import SafeCodeAgent
from agents.runtime.controller import SafePythonExecutor
from agents.runtime.policy import ImportStatus

class TestRuntimeAgent(unittest.TestCase):
    def setUp(self):
        self.mock_model = MagicMock()
        self.tools = []

    @patch("smolagents.CodeAgent.create_python_executor")
    def test_agent_initialization(self, mock_create_executor):
        mock_executor = MagicMock()
        mock_executor.state = {"__name__": "__main__"}
        mock_create_executor.return_value = mock_executor
        
        agent = SafeCodeAgent(
            model=self.mock_model,
            tools=self.tools,
            additional_authorized_imports=["math"]
        )
        
        self.assertIn("RUNTIME ENVIRONMENT CAPABILITIES & CONSTRAINTS", agent.prompt_templates["system_prompt"])
        self.isinstance = isinstance(agent.python_executor, SafePythonExecutor)
        self.assertTrue(self.isinstance)
        self.assertIn("math", agent.policy_manager.additional_authorized_imports)
        self.assertIn("json", agent.policy_manager.additional_authorized_imports)
        self.assertIn("csv", agent.policy_manager.additional_authorized_imports)

    def test_safe_executor_static_rewrite_and_run(self):
        underlying = MagicMock()
        def mock_run(code):
            if "agents.runtime.fallbacks.requests_fallback" in code:
                return CodeOutput(output="success", logs="run logs", is_final_answer=True)
            raise Exception("Did not rewrite requests import!")
            
        underlying.side_effect = mock_run
        underlying.state = {"__name__": "__main__"}
        underlying.additional_authorized_imports = []
        underlying.authorized_imports = []

        agent = SafeCodeAgent(
            model=self.mock_model,
            tools=self.tools
        )
        
        safe_executor = SafePythonExecutor(
            agent=agent,
            underlying_executor=underlying,
            max_retries=2
        )
        
        code = "import requests\nr = requests.get('http://test.com')\nfinal_answer(r.text)"
        out = safe_executor(code)
        
        self.assertEqual(out.output, "success")
        self.assertEqual(safe_executor.metrics.validations_total, 2)
        self.assertEqual(safe_executor.metrics.static_rewrites, 1)
        self.assertEqual(safe_executor.metrics.execution_successes, 1)

    def test_safe_executor_llm_regeneration_recovery(self):
        underlying = MagicMock()
        underlying.state = {"__name__": "__main__"}
        
        def mock_run(code):
            if "valid_code" in code:
                return CodeOutput(output="recovered", logs="ok", is_final_answer=True)
            raise Exception("Invalid code executed")
        underlying.side_effect = mock_run

        agent = SafeCodeAgent(
            model=self.mock_model,
            tools=self.tools
        )
        
        mock_response = MagicMock()
        mock_response.content = "```python\n# valid_code\nfinal_answer('recovered')\n```"
        self.mock_model.return_value = mock_response

        safe_executor = SafePythonExecutor(
            agent=agent,
            underlying_executor=underlying,
            max_retries=2
        )
        
        bad_syntax_code = "def bad_func(:"
        
        out = safe_executor(bad_syntax_code)
        
        self.assertEqual(out.output, "recovered")
        self.assertEqual(safe_executor.metrics.llm_regenerations, 1)
        self.assertEqual(safe_executor.metrics.validation_failures, 1)
        self.assertEqual(safe_executor.metrics.execution_successes, 1)

    def test_write_memory_to_messages_with_lessons(self):
        agent = SafeCodeAgent(
            model=self.mock_model,
            tools=self.tools
        )
        
        # Add an error to memory
        agent.error_memory.add_error("import json", "ValidationError_UNAUTHORIZED_IMPORT", "Import of json is not allowed.")
        
        messages = agent.write_memory_to_messages()
        
        # Ensure message content can be processed by get_clean_message_list without assertion errors
        cleaned = get_clean_message_list(messages)
        self.assertTrue(len(cleaned) > 0)
        
        # Verify lessons prompt is injected into system message content
        sys_text = str(cleaned[0]["content"])
        self.assertIn("LEARNED RUNTIME CONSTRAINTS & LIMITATIONS", sys_text)
