from typing import Any, Dict, List, Optional
from smolagents import CodeAgent
from smolagents.local_python_executor import PythonExecutor

from agents.runtime.discovery import RuntimeCapabilityManager
from agents.runtime.policy import ImportPolicyManager
from agents.runtime.validator import CodeValidationEngine
from agents.runtime.compatibility import ExecutionCompatibilityLayer
from agents.runtime.learning import ErrorLearningMemory
from agents.runtime.metrics import SafetyMetricsCollector
from agents.runtime.controller import SafePythonExecutor

class SafeCodeAgent(CodeAgent):
    """
    An enhanced CodeAgent that ensures all generated code is executable within the
    current runtime environment, checking imports, APIs, tools, and learning from errors.
    """

    def __init__(self, *args, **kwargs):
        authorized_imports = list(kwargs.get("additional_authorized_imports", []))
        
        # Ensure standard utility modules like json and csv are authorized by default
        for default_pkg in ["json", "csv"]:
            if default_pkg not in authorized_imports:
                authorized_imports.append(default_pkg)
                
        kwargs["additional_authorized_imports"] = authorized_imports

        self.policy_manager = ImportPolicyManager(authorized_imports)
        self.capability_manager = RuntimeCapabilityManager(self)
        self.validator = CodeValidationEngine(self.policy_manager)
        self.compatibility_layer = ExecutionCompatibilityLayer()
        self.error_memory = ErrorLearningMemory()
        self.metrics = SafetyMetricsCollector()
        
        super().__init__(*args, **kwargs)
        
        caps_prompt = self.capability_manager.generate_capability_prompt()
        if hasattr(self, "prompt_templates") and "system_prompt" in self.prompt_templates:
            self.prompt_templates["system_prompt"] += f"\n\n{caps_prompt}\n"

    def create_python_executor(self) -> PythonExecutor:
        """Overrides the standard executor creation to insert the SafePythonExecutor wrapper."""
        standard_executor = super().create_python_executor()
        return SafePythonExecutor(
            agent=self,
            underlying_executor=standard_executor,
            max_retries=3,
            capability_manager=self.capability_manager,
            validator=self.validator,
            compatibility_layer=self.compatibility_layer,
            error_memory=self.error_memory,
            metrics=self.metrics
        )

    def write_memory_to_messages(self, summary_mode: bool = False) -> List[Any]:
        """Injects dynamic execution lessons cleanly into the system prompt message content."""
        messages = super().write_memory_to_messages(summary_mode=summary_mode)
        
        lessons_prompt = self.error_memory.get_lessons_prompt()
        if lessons_prompt and messages:
            sys_content = messages[0].content
            if isinstance(sys_content, list) and len(sys_content) > 0 and isinstance(sys_content[0], dict) and "text" in sys_content[0]:
                sys_content[0]["text"] += f"\n\n{lessons_prompt}"
            elif isinstance(sys_content, str):
                messages[0].content = f"{sys_content}\n\n{lessons_prompt}"
            else:
                from smolagents.memory import ChatMessage
                from smolagents.models import MessageRole
                lessons_msg = ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=[{"type": "text", "text": lessons_prompt}]
                )
                messages.insert(1, lessons_msg)
            
        return messages
