"""ProcessingPipeline execution engine."""

import time
from tools.document.interfaces.pipeline import IProcessingPipeline, IPipelineRegistry
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext
from tools.document.exceptions import PipelineExecutionError
from infrastructure.logging.logger import StructuredLogger


class ProcessingPipeline(IProcessingPipeline):
    """Executes registered IPipelineSteps sequentially on NormalizedDocument."""

    def __init__(self, pipeline_registry: IPipelineRegistry) -> None:
        self._logger = StructuredLogger("ProcessingPipeline")
        self.pipeline_registry = pipeline_registry

    async def execute(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        """Execute registered pipeline steps."""
        steps = self.pipeline_registry.get_steps()
        self._logger.info(f"Starting processing pipeline execution ({len(steps)} steps)")

        for step in steps:
            if context.cancelled:
                self._logger.warning("Pipeline execution cancelled.")
                break

            step_start = time.time()
            try:
                document = await step.process(document, context)
                elapsed_ms = (time.time() - step_start) * 1000.0
                document.processing_history.append({
                    "step": step.name,
                    "status": "success",
                    "duration_ms": elapsed_ms,
                })
                self._logger.debug(f"Step '{step.name}' completed in {elapsed_ms:.2f} ms")
            except Exception as e:
                elapsed_ms = (time.time() - step_start) * 1000.0
                document.processing_history.append({
                    "step": step.name,
                    "status": "failed",
                    "error": str(e),
                    "duration_ms": elapsed_ms,
                })
                self._logger.error(f"Step '{step.name}' failed: {e}")
                context.add_warning(f"Step '{step.name}' error: {e}")
                raise PipelineExecutionError(step.name, str(e)) from e

        return document
