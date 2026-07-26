from typing import Dict, Any, List

class ErrorLearningMemory:
    """
    Maintains a log of errors encountered during execution, compiles these
    into actionable lessons, and monitors for repeating failure loops.
    """

    def __init__(self, max_consecutive_failures: int = 3):
        self.max_consecutive_failures = max_consecutive_failures
        self.errors_history: List[Dict[str, Any]] = []
        self.consecutive_failures: List[str] = []

    def add_error(self, code: str, error_type: str, message: str, context: str = None):
        """Logs an execution or validation failure and tracks execution counters."""
        error_entry = {
            "code": code,
            "error_type": error_type,
            "message": message,
            "context": context
        }
        self.errors_history.append(error_entry)
        
        signature = f"{error_type}:{message}"
        self.consecutive_failures.append(signature)

    def detect_loop(self) -> bool:
        """Returns True if the identical error has occurred repeatedly."""
        if len(self.consecutive_failures) < self.max_consecutive_failures:
            return False
            
        recent = self.consecutive_failures[-self.max_consecutive_failures:]
        return len(set(recent)) == 1

    def clear_consecutive_failures(self):
        """Resets the consecutive failures counter, typically called on success."""
        self.consecutive_failures.clear()

    def get_lessons(self) -> List[str]:
        """Synthesizes unique lessons learned from past errors."""
        lessons = []
        seen_messages = set()
        
        for err in self.errors_history:
            msg = err["message"]
            err_type = err["error_type"]
            
            if msg in seen_messages:
                continue
            seen_messages.add(msg)
            
            if "unauthorized import" in msg.lower() or "is not allowed" in msg.lower():
                lessons.append(f"Importing this package is restricted by sandboxing rules: {msg}")
            elif "not installed" in msg.lower() or "missing_library" in err_type.lower() or "modulenotfounderror" in err_type.lower():
                lessons.append(f"The package is not installed. Solve the task using only standard libraries: {msg}")
            elif "signature match failed" in msg.lower() or "invalid_tool_usage" in err_type.lower():
                lessons.append(f"Tool signature issue: {msg}")
            elif "outside the authorized workspace" in msg.lower() or "out_of_bounds_path" in err_type.lower():
                lessons.append(f"File access violation: {msg}. Stay inside workspace.")
            elif "syntax error" in msg.lower() or "syntax_error" in err_type.lower():
                lessons.append(f"Generated python code had syntax compilation errors: {msg}")
            else:
                lessons.append(f"Code failed at runtime: {msg}")
                
        return lessons

    def get_lessons_prompt(self) -> str:
        """Formats the learned lessons as a system instructions helper."""
        lessons = self.get_lessons()
        if not lessons:
            return ""
            
        prompt = "\n### LEARNED RUNTIME CONSTRAINTS & LIMITATIONS (DO NOT REPEAT THESE ERRORS):\n"
        for i, lesson in enumerate(lessons, 1):
            prompt += f"{i}. {lesson}\n"
        prompt += "Adjust your coding strategy to work around these limitations.\n"
        return prompt

    def clear(self):
        """Clears all logged memory."""
        self.errors_history.clear()
        self.consecutive_failures.clear()
        
    def get_consecutive_failures_count(self) -> int:
        """Returns the current number of recorded consecutive failures."""
        return len(self.consecutive_failures)
