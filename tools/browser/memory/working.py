"""Working Memory layer for active session state."""

import time
from typing import Dict, Any, List

from tools.browser.memory.models import MemoryItem, MemoryType
from tools.browser.state_manager import BrowserStateSnapshot


class WorkingMemory:
    """Short-term, volatile storage holding the current active goal, variables, and state.
    
    This memory is cleared or summarized when a task completes. It does not
    use a vector store because it is meant for exact key-value retrieval
    and short-term chronological context.
    """

    def __init__(self, max_recent_steps: int = 10):
        self.active_goal: str = ""
        self.variables: Dict[str, Any] = {}
        self.recent_steps: List[Dict[str, Any]] = []
        self.max_recent_steps = max_recent_steps
        self.current_state: BrowserStateSnapshot = None
        self.start_time: float = time.time()

    def set_goal(self, goal: str) -> None:
        self.active_goal = goal
        self.start_time = time.time()

    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def log_step(self, action: Dict[str, Any], success: bool, result_msg: str) -> None:
        step = {
            "timestamp": time.time(),
            "action": action,
            "success": success,
            "result": result_msg,
        }
        self.recent_steps.append(step)
        if len(self.recent_steps) > self.max_recent_steps:
            self.recent_steps.pop(0)

    def update_state(self, state: BrowserStateSnapshot) -> None:
        self.current_state = state

    def clear(self) -> None:
        """Reset working memory for a new task."""
        self.active_goal = ""
        self.variables.clear()
        self.recent_steps.clear()
        self.current_state = None
        self.start_time = time.time()

    def summarize(self) -> MemoryItem:
        """Compress the working memory into an episodic summary item."""
        duration = time.time() - self.start_time
        success_count = sum(1 for s in self.recent_steps if s["success"])
        
        content = f"Goal: {self.active_goal}\n"
        content += f"Duration: {duration:.1f}s\n"
        content += f"Steps: {len(self.recent_steps)} ({success_count} successful)\n"
        
        return MemoryItem(
            content=content,
            memory_type=MemoryType.WORKING,
            importance=0.5,
            metadata={"duration": duration, "goal": self.active_goal}
        )
