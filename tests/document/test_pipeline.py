"""Unit tests for PipelineRegistry, ProcessingPipeline, and Pipeline Steps."""

import asyncio
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext
from tools.document.pipeline.registry import PipelineRegistry
from tools.document.pipeline.engine import ProcessingPipeline
from tools.document.pipeline.cleaner import CleanerStep
from tools.document.pipeline.header_footer import HeaderFooterStep
from tools.document.pipeline.metadata_extractor import MetadataExtractorStep
from tools.document.pipeline.heading_detector import HeadingDetectorStep
from tools.document.pipeline.chunker import ChunkerStep


def test_processing_pipeline_execution():
    async def _test():
        registry = PipelineRegistry()
        registry.register_step(CleanerStep())
        registry.register_step(HeaderFooterStep())
        registry.register_step(MetadataExtractorStep())
        registry.register_step(HeadingDetectorStep())
        registry.register_step(ChunkerStep())

        pipeline = ProcessingPipeline(pipeline_registry=registry)
        ctx = ProcessingContext()

        doc = NormalizedDocument()
        doc.full_text = "# Main Header\n\nThis is paragraph content text.\n\n# Second Header\n\nSecond paragraph content text."

        processed_doc = await pipeline.execute(doc, ctx)

        assert processed_doc.metadata.word_count > 0
        assert len(processed_doc.sections) == 2
        assert len(processed_doc.chunks) > 0
        assert len(processed_doc.processing_history) == 5

    asyncio.run(_test())
