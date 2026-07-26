import unittest
from agents.runtime.learning import ErrorLearningMemory

class TestRuntimeLearning(unittest.TestCase):
    def test_error_tracking(self):
        memory = ErrorLearningMemory(max_consecutive_failures=3)
        
        memory.add_error("import pandas", "ValidationError_MISSING_LIBRARY", "pandas is not installed.")
        lessons = memory.get_lessons()
        self.assertEqual(len(lessons), 1)
        self.assertIn("pandas is not installed", lessons[0])

    def test_loop_detection(self):
        memory = ErrorLearningMemory(max_consecutive_failures=3)
        
        memory.add_error("click()", "RuntimeError", "Element not clickable")
        self.assertFalse(memory.detect_loop())

        memory.add_error("click()", "RuntimeError", "Element not clickable")
        self.assertFalse(memory.detect_loop())

        memory.add_error("click()", "RuntimeError", "Element not clickable")
        self.assertTrue(memory.detect_loop())

        memory.clear_consecutive_failures()
        self.assertFalse(memory.detect_loop())

    def test_lessons_prompt_generation(self):
        memory = ErrorLearningMemory()
        memory.add_error("import subprocess", "ValidationError_UNAUTHORIZED_IMPORT", "Import of subprocess is blocked")
        
        prompt = memory.get_lessons_prompt()
        self.assertIn("LEARNED RUNTIME CONSTRAINTS", prompt)
        self.assertIn("subprocess is blocked", prompt)
