"""Pipeline Registry managing ordered document processing steps."""

from typing import List, Optional, Dict
from tools.document.interfaces.pipeline import IPipelineStep, IPipelineRegistry
from infrastructure.logging.logger import StructuredLogger


class PipelineRegistry(IPipelineRegistry):
    """Manages ordered plugin pipeline steps."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("PipelineRegistry")
        self._steps: List[IPipelineStep] = []

    def register_step(self, step: IPipelineStep, index: Optional[int] = None) -> None:
        """Register a pipeline step, optionally at a specific index."""
        if index is not None and 0 <= index <= len(self._steps):
            self._steps.insert(index, step)
        else:
            self._steps.append(step)
        self._logger.debug(f"Registered pipeline step '{step.name}' at position {len(self._steps) - 1}")

    def unregister_step(self, step_name: str) -> bool:
        """Unregister a step by its name."""
        initial_len = len(self._steps)
        self._steps = [s for s in self._steps if s.name != step_name]
        removed = len(self._steps) < initial_len
        if removed:
            self._logger.debug(f"Unregistered pipeline step '{step_name}'")
        return removed

    def get_steps(self) -> List[IPipelineStep]:
        """Return shallow copy of ordered pipeline steps."""
        return list(self._steps)
