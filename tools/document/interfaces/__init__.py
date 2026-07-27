"""Interfaces for Document Intelligence Platform."""

from tools.document.interfaces.detector import IFormatDetector
from tools.document.interfaces.parser import IDocumentParser, IParserRegistry
from tools.document.interfaces.router import IFileRouter
from tools.document.interfaces.pipeline import IPipelineStep, IPipelineRegistry, IProcessingPipeline
from tools.document.interfaces.artifact_manager import IDocumentArtifactManager
from tools.document.interfaces.retrieval import (
    IRetrievalEngine,
    IDocumentComparator,
    IDocumentSummarizer,
    IVectorSearchEngine,
)

__all__ = [
    "IFormatDetector",
    "IDocumentParser",
    "IParserRegistry",
    "IFileRouter",
    "IPipelineStep",
    "IPipelineRegistry",
    "IProcessingPipeline",
    "IDocumentArtifactManager",
    "IRetrievalEngine",
    "IDocumentComparator",
    "IDocumentSummarizer",
    "IVectorSearchEngine",
]
