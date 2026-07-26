import time
import logging
from typing import Any, List, Optional
from smolagents.local_python_executor import PythonExecutor, CodeOutput
from agents.runtime.discovery import RuntimeCapabilityManager
from agents.runtime.validator import CodeValidationEngine
from agents.runtime.compatibility import ExecutionCompatibilityLayer
from agents.runtime.learning import ErrorLearningMemory
from agents.runtime.metrics import SafetyMetricsCollector

logger = logging.getLogger("SafePythonExecutor")

class SafePythonExecutor(PythonExecutor):
    """
    Wraps standard PythonExecutor execution with static AST validation,
    import checking, automated shimming/rewriting, and dynamic LLM regeneration retries.
    """

    def __init__(
        self,
        agent: Any,
        underlying_executor: PythonExecutor,
        max_retries: int = 3,
        capability_manager: Optional[RuntimeCapabilityManager] = None,
        validator: Optional[CodeValidationEngine] = None,
        compatibility_layer: Optional[ExecutionCompatibilityLayer] = None,
        error_memory: Optional[ErrorLearningMemory] = None,
        metrics: Optional[SafetyMetricsCollector] = None,
    ):
        self.agent = agent
        self.underlying_executor = underlying_executor
        self.max_retries = max_retries
        
        self.capability_manager = capability_manager or RuntimeCapabilityManager(agent)
        self.validator = validator or CodeValidationEngine(agent.policy_manager)
        self.compatibility_layer = compatibility_layer or ExecutionCompatibilityLayer()
        self.error_memory = error_memory or ErrorLearningMemory()
        self.metrics = metrics or SafetyMetricsCollector()

        # Copy state and parameters to align with CodeAgent requirements
        self.state = getattr(underlying_executor, "state", {"__name__": "__main__"})
        self.additional_authorized_imports = getattr(underlying_executor, "additional_authorized_imports", [])
        self.authorized_imports = getattr(underlying_executor, "authorized_imports", [])

    def send_tools(self, tools: list) -> None:
        """Delegates tools update to the underlying executor."""
        self.underlying_executor.send_tools(tools)

    def send_variables(self, variables: dict) -> None:
        """Delegates variables update to the underlying executor."""
        self.underlying_executor.send_variables(variables)

    def __call__(self, code_action: str) -> CodeOutput:
        """
        Validates, potentially rewrites/regenerates, and runs python code.
        """
        start_time = time.time()
        current_code = code_action
        retry_count = 0
        
        while retry_count <= self.max_retries:
            self.metrics.increment_validations()
            
            # Static check
            val_start = time.time()
            validation_result = self.validator.validate(current_code, self.agent.tools)
            self.metrics.record_time(time.time() - val_start)
            
            # If warnings (restricted imports) or errors are present, try static AST rewriting
            if validation_result.warnings or not validation_result.is_valid:
                rewrite_start = time.time()
                rewritten = self.compatibility_layer.rewrite_statically(current_code, validation_result)
                self.metrics.record_time(time.time() - rewrite_start)
                
                if rewritten and rewritten != current_code:
                    logger.info(f"Statically rewrote code chunk. Re-validating new AST...")
                    self.metrics.increment_rewrites()
                    current_code = rewritten
                    continue
            
            # If code is still not valid after trying to rewrite, process errors
            if not validation_result.is_valid:
                self.metrics.increment_validation_failures()
                errors = [err.message for err in validation_result.errors]
                logger.warning(f"Static validation failed for code:\n{current_code}\nErrors: {errors}")
                
                # Add validation errors to memory
                for err in validation_result.errors:
                    self.error_memory.add_error(
                        code=current_code,
                        error_type=f"ValidationError_{err.code}",
                        message=err.message,
                        context=f"Line {err.line}, Col {err.col}"
                    )
                
                if retry_count == self.max_retries:
                    err_msg = f"Code block failed validation checks after {self.max_retries} attempts: {errors}"
                    self.metrics.record_time(time.time() - start_time)
                    raise Exception(err_msg)
                
                if self.error_memory.detect_loop():
                    err_msg = f"Loop detected: Code generator is repeating identical validation failures."
                    self.metrics.record_time(time.time() - start_time)
                    raise Exception(err_msg)
                
                # LLM-based regeneration
                self.metrics.increment_regenerations()
                correction_prompt = self.generate_correction_prompt(current_code, errors)
                logger.info(f"Regenerating code via LLM (Attempt {retry_count + 1}/{self.max_retries})...")
                
                regen_start = time.time()
                current_code = self.regenerate_code(correction_prompt)
                self.metrics.record_time(time.time() - regen_start)
                
                retry_count += 1
                continue
            
            # Static check passed, try execution
            try:
                if hasattr(self.underlying_executor, "state"):
                    self.underlying_executor.state = self.state
                
                code_output = self.underlying_executor(current_code)
                
                if hasattr(self.underlying_executor, "state"):
                    self.state = self.underlying_executor.state
                
                self.error_memory.clear_consecutive_failures()
                self.metrics.increment_execution_successes()
                self.metrics.record_time(time.time() - start_time)
                return code_output
                
            except Exception as execution_err:
                self.metrics.increment_execution_failures()
                err_msg = str(execution_err)
                logger.error(f"Runtime execution failed: {err_msg}")
                
                self.error_memory.add_error(
                    code=current_code,
                    error_type="RuntimeError",
                    message=err_msg,
                    context=execution_err.__class__.__name__
                )
                
                if retry_count == self.max_retries:
                    self.metrics.record_time(time.time() - start_time)
                    raise execution_err
                
                if self.error_memory.detect_loop():
                    err_msg_loop = f"Loop detected: repeating consecutive runtime errors. Stopping execution. Last error: {err_msg}"
                    self.metrics.record_time(time.time() - start_time)
                    raise Exception(err_msg_loop)
                
                self.metrics.increment_regenerations()
                errors = [f"Runtime error: {err_msg}"]
                correction_prompt = self.generate_correction_prompt(current_code, errors, traceback_str=err_msg)
                logger.info(f"Regenerating code via LLM due to runtime failure (Attempt {retry_count + 1}/{self.max_retries})...")
                
                regen_start = time.time()
                current_code = self.regenerate_code(correction_prompt)
                self.metrics.record_time(time.time() - regen_start)
                
                retry_count += 1

        self.metrics.record_time(time.time() - start_time)
        return CodeOutput(output="", logs="Max retries reached without execution.", is_final_answer=False)

    def generate_correction_prompt(self, invalid_code: str, errors: List[str], traceback_str: Optional[str] = None) -> str:
        """Formats the detailed error description prompt for LLM-based repairs."""
        caps_str = self.capability_manager.generate_capability_prompt()
        lessons_str = self.error_memory.get_lessons_prompt()
        
        prompt = f"""
You generated a Python code block which is invalid or failed to execute in the current runtime environment:

```python
{invalid_code}
```

### Errors Detected
{chr(10).join(f"- {e}" for e in errors)}
"""
        if traceback_str:
            prompt += f"\n### Runtime Traceback\n{traceback_str}\n"

        prompt += f"""
{caps_str}
{lessons_str}

### Instructions
Please rewrite the invalid python code block to fix the errors listed above.
Verify your imports and tool argument names. Remember:
1. Only call helper tools with correct keyword arguments matching their definition.
2. Only import authorized modules. If a library like requests, pandas, or numpy is restricted, use standard modules instead (like urllib.request, csv, math).
3. Ensure syntax is clean and valid.
4. If you have the final answer, call `final_answer(result)` inside the code block.

Respond ONLY with a valid Python code block starting with ```python and ending with ```. Do not provide any comments or summaries outside the code block.
"""
        return prompt

    def regenerate_code(self, prompt: str) -> str:
        """Calls the agent model to regenerate corrected code action."""
        try:
            messages = [{"role": "user", "content": prompt}]
            chat_message = self.agent.model(messages)
            content = chat_message.content
            
            # Handle mock fallback in tests if content is not string
            if not isinstance(content, str):
                content = str(content)
            
            from smolagents import extract_code_from_text
            tags = getattr(self.agent, "code_block_tags", ("```python", "```"))
            
            # Robust code block extraction
            code = None
            if tags:
                code = extract_code_from_text(content, tags)
            
            if not code:
                code = extract_code_from_text(content, ("```python", "```"))
                
            if not code:
                code = extract_code_from_text(content, ("```", "```"))
                
            if not code:
                if "```python" in content:
                    parts = content.split("```python")
                    if len(parts) > 1:
                        code = parts[1].split("```")[0].strip()
                elif "```" in content:
                    parts = content.split("```")
                    if len(parts) > 1:
                        code = parts[1].split("```")[0].strip()
                        
            if not code:
                code = content
                
            return code.strip()
        except Exception as e:
            logger.exception("Failed to regenerate code using LLM")
            raise RuntimeError(f"Error during LLM code correction: {e}")
