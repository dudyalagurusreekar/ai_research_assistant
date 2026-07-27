"""Processing Pipeline & Step Interfaces."""

from abc import ABC, abstractmethod
from typing import List, Optional
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext


class IPipelineStep(ABC):
    """Interface for a single document processing pipeline step."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the pipeline step."""
        pass

    @abstractmethod
    async def process(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        """Execute step logic on NormalizedDocument."""
        pass


class IPipelineRegistry(ABC):
    """Interface for managing registered pipeline steps."""

    @abstractmethod
    def register_step(self, step: IPipelineStep, index: Optional[int] = None) -> None:
        """Register a pipeline step."""
        pass

    @abstractmethod
    def unregister_step(self, step_name: str) -> bool:
        """Unregister a step by name."""
        pass

    @abstractmethod
    def get_steps(self) -> List[IPipelineStep]:
        """Get ordered list of pipeline steps."""
        pass


class IProcessingPipeline(ABC):
    """Interface for Document Processing Pipeline execution engine."""

    @abstractmethod
    async def execute(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        """Execute all registered pipeline steps on NormalizedDocument."""
        pass
