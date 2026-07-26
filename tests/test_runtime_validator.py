import unittest
from pathlib import Path
from unittest.mock import MagicMock
from agents.runtime.policy import ImportPolicyManager
from agents.runtime.validator import CodeValidationEngine

class TestRuntimeValidator(unittest.TestCase):
    def setUp(self):
        self.policy_manager = ImportPolicyManager()
        self.workspace = Path("d:/AI-Research-Assistant").resolve()
        self.validator = CodeValidationEngine(self.policy_manager, self.workspace)
        
        self.mock_tool = MagicMock()
        self.mock_tool.name = "web_search"
        def forward(query: str, limit: int = 10):
            pass
        self.mock_tool.forward = forward
        self.tools = {"web_search": self.mock_tool}

    def test_syntax_validation(self):
        bad_code = "def my_func(:"
        res = self.validator.validate(bad_code, self.tools)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.errors[0].code, "SYNTAX_ERROR")

    def test_blocked_builtins(self):
        eval_code = "eval('5 + 3')"
        res = self.validator.validate(eval_code, self.tools)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.errors[0].code, "BLOCKED_BUILTIN")

    def test_unauthorized_imports(self):
        bad_import = "import subprocess"
        res = self.validator.validate(bad_import, self.tools)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.errors[0].code, "UNAUTHORIZED_IMPORT")

    def test_invalid_tool_calls(self):
        bad_call_1 = "web_search()"
        res = self.validator.validate(bad_call_1, self.tools)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.errors[0].code, "INVALID_TOOL_USAGE")

        bad_call_2 = "web_search(search_query='test')"
        res = self.validator.validate(bad_call_2, self.tools)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.errors[0].code, "INVALID_TOOL_USAGE")

        valid_call = "web_search(query='test', limit=5)"
        res = self.validator.validate(valid_call, self.tools)
        self.assertTrue(res.is_valid)

    def test_path_safety(self):
        bad_path_win = "file = 'C:/Windows/System32/cmd.exe'"
        res = self.validator.validate(bad_path_win, self.tools)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.errors[0].code, "OUT_OF_BOUNDS_PATH")
        
        good_path = "file = 'd:/AI-Research-Assistant/data/report.txt'"
        res = self.validator.validate(good_path, self.tools)
        self.assertTrue(res.is_valid)
